from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Card, Deck, DeckResult


def make_deck(title="Django Terms", **kwargs):
    return Deck.objects.create(title=title, **kwargs)


def make_cards(deck, n=3):
    return [
        Card.objects.create(
            deck=deck, term=f"term {i}", definition=f"definition {i}", position=i
        )
        for i in range(1, n + 1)
    ]


class ModelTests(TestCase):
    def test_slug_generated(self):
        self.assertEqual(make_deck().slug, "django-terms")

    def test_result_percentage(self):
        deck = make_deck()
        User = get_user_model()
        user = User.objects.create_user("u", password="x")
        r = DeckResult.objects.create(deck=deck, user=user, known_count=3, missed_count=1)
        self.assertEqual(r.total, 4)
        self.assertEqual(r.percentage, 75.0)
        self.assertTrue(r.passed)


class ViewTests(TestCase):
    def setUp(self):
        self.deck = make_deck()
        self.cards = make_cards(self.deck, 3)
        User = get_user_model()
        self.user = User.objects.create_user("student", password="pass12345")

    def test_list_shows_published_only(self):
        make_deck(title="Hidden Deck", is_published=False)
        resp = self.client.get(reverse("deck-list"))
        self.assertContains(resp, "Django Terms")
        self.assertNotContains(resp, "Hidden Deck")

    def test_detail_hidden_deck_404(self):
        hidden = make_deck(title="Hidden Two", is_published=False)
        resp = self.client.get(reverse("deck-detail", args=[hidden.slug]))
        self.assertEqual(resp.status_code, 404)

    def test_detail_shows_cards(self):
        resp = self.client.get(reverse("deck-detail", args=[self.deck.slug]))
        self.assertContains(resp, "term 1")
        self.assertContains(resp, "definition 3")

    def test_study_requires_login(self):
        resp = self.client.get(reverse("deck-study", args=[self.deck.slug]))
        self.assertRedirects(
            resp,
            f"{reverse('login')}?next={reverse('deck-study', args=[self.deck.slug])}",
        )

    def test_study_flow_completes_and_records_result(self):
        self.client.login(username="student", password="pass12345")
        resp = self.client.get(reverse("deck-study", args=[self.deck.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Card 1 of 3")

        marks = ["known", "missed", "known"]
        for i, mark in enumerate(marks):
            resp = self.client.post(
                reverse("deck-mark", args=[self.deck.slug]), {"mark": mark}
            )
            if i < 2:
                self.assertRedirects(
                    resp, reverse("deck-study", args=[self.deck.slug])
                )

        result = DeckResult.objects.get()
        self.assertEqual(result.known_count, 2)
        self.assertEqual(result.missed_count, 1)
        self.assertEqual(result.percentage, 66.7)
        resp = self.client.get(reverse("deck-detail", args=[self.deck.slug]))
        self.assertContains(resp, "2/3")

    def test_study_uses_all_cards_once(self):
        self.client.login(username="student", password="pass12345")
        self.client.get(reverse("deck-study", args=[self.deck.slug]))
        seen = []
        for _ in range(3):
            resp = self.client.post(reverse("deck-mark", args=[self.deck.slug]), {"mark": "known"})
            seen.append(resp)
        result = DeckResult.objects.get()
        self.assertEqual(result.known_count, 3)
        self.assertEqual(result.missed_count, 0)

    def test_mark_without_session_redirects(self):
        self.client.login(username="student", password="pass12345")
        resp = self.client.post(
            reverse("deck-mark", args=[self.deck.slug]), {"mark": "known"}
        )
        self.assertRedirects(resp, reverse("deck-study", args=[self.deck.slug]))
        self.assertFalse(DeckResult.objects.exists())

    def test_empty_deck_study_redirects(self):
        empty = make_deck(title="Empty Deck")
        self.client.login(username="student", password="pass12345")
        resp = self.client.get(reverse("deck-study", args=[empty.slug]))
        self.assertRedirects(resp, reverse("deck-detail", args=[empty.slug]))


class SeedTests(TestCase):
    def test_seed_flashcards_idempotent(self):
        from django.core.management import call_command

        call_command("seed_flashcards")
        call_command("seed_flashcards")
        self.assertEqual(Deck.objects.count(), 2)
        self.assertGreater(Card.objects.count(), 0)
