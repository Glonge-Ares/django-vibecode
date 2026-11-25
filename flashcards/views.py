import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Card, Deck, DeckResult

SESSION_PREFIX = "flashcard_study:"
MARKS = ("known", "missed")


def deck_list(request):
    decks = Deck.objects.filter(is_published=True).prefetch_related("cards")
    entries = []
    for deck in decks:
        entry = {"deck": deck, "card_count": deck.cards.count(), "last_result": None}
        if request.user.is_authenticated:
            entry["last_result"] = (
                DeckResult.objects.filter(user=request.user, deck=deck)
                .order_by("-created_at")
                .first()
            )
        entries.append(entry)
    return render(request, "flashcards/deck_list.html", {"entries": entries})


def _get_published_deck(slug):
    deck = get_object_or_404(Deck, slug=slug)
    if not deck.is_published:
        raise Http404
    return deck


def deck_detail(request, slug):
    deck = _get_published_deck(slug)
    results = []
    if request.user.is_authenticated:
        results = DeckResult.objects.filter(user=request.user, deck=deck)[:5]
    return render(
        request,
        "flashcards/deck_detail.html",
        {"deck": deck, "cards": deck.cards.all(), "results": results},
    )


def _load_state(request, deck):
    key = SESSION_PREFIX + deck.slug
    state = request.session.get(key)
    if (
        not isinstance(state, dict)
        or not state.get("queue")
        or state.get("idx", 0) >= len(state["queue"])
    ):
        return None
    return state


def _new_state(deck):
    card_ids = list(deck.cards.values_list("id", flat=True))
    return {
        "queue": random.sample(card_ids, len(card_ids)),
        "idx": 0,
        "known": [],
        "missed": [],
    }


@login_required
def deck_study(request, slug):
    deck = _get_published_deck(slug)
    if not deck.cards.exists():
        messages.warning(request, "This deck has no cards yet.")
        return redirect("deck-detail", slug=deck.slug)

    state = _load_state(request, deck)
    if state is None:
        state = _new_state(deck)
        request.session[SESSION_PREFIX + deck.slug] = state

    card = get_object_or_404(Card, pk=state["queue"][state["idx"]], deck=deck)
    return render(
        request,
        "flashcards/study.html",
        {
            "deck": deck,
            "card": card,
            "position": state["idx"] + 1,
            "total": len(state["queue"]),
            "known_so_far": len(state["known"]),
            "missed_so_far": len(state["missed"]),
        },
    )


@require_POST
@login_required
def deck_study_mark(request, slug):
    deck = _get_published_deck(slug)
    state = _load_state(request, deck)
    if state is None:
        return redirect("deck-study", slug=deck.slug)

    mark = request.POST.get("mark")
    if mark not in MARKS:
        messages.error(request, "Unknown mark.")
        return redirect("deck-study", slug=deck.slug)

    card_id = state["queue"][state["idx"]]
    state["known" if mark == "known" else "missed"].append(card_id)
    state["idx"] += 1

    if state["idx"] >= len(state["queue"]):
        result = DeckResult.objects.create(
            deck=deck,
            user=request.user,
            known_count=len(state["known"]),
            missed_count=len(state["missed"]),
        )
        del request.session[SESSION_PREFIX + deck.slug]
        messages.success(
            request,
            f"Finished «{deck.title}»: {result.known_count}/{result.total} known "
            f"({result.percentage}%).",
        )
        return redirect("deck-detail", slug=deck.slug)

    request.session[SESSION_PREFIX + deck.slug] = state
    return redirect("deck-study", slug=deck.slug)
