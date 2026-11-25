from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Answer, Attempt, Choice, Exam, Question


def make_exam(title="Algebra Basics", **kwargs):
    return Exam.objects.create(title=title, **kwargs)


def make_single_question(exam, text="2 + 2 = ?"):
    q = Question.objects.create(exam=exam, text=text, kind=Question.Kind.SINGLE, points=2)
    Choice.objects.create(question=q, text="3", is_correct=False)
    Choice.objects.create(question=q, text="4", is_correct=True)
    Choice.objects.create(question=q, text="5", is_correct=False)
    return q


class ModelTests(TestCase):
    def test_slug_generated_and_unique(self):
        a = make_exam(title="Same Title")
        b = make_exam(title="Same Title!")
        self.assertEqual(a.slug, "same-title")
        self.assertEqual(b.slug, "same-title-2")

    def test_total_points(self):
        exam = make_exam()
        make_single_question(exam)
        Question.objects.create(
            exam=exam,
            text="Name a prime.",
            kind=Question.Kind.TEXT,
            points=3,
            expected_text="7",
        )
        self.assertEqual(exam.total_points, 5)

    def test_single_choice_grading(self):
        exam = make_exam()
        q = make_single_question(exam)
        right = q.choices.get(is_correct=True)
        wrong = q.choices.get(text="3")
        self.assertTrue(q.is_correctly_answered([right.pk], ""))
        self.assertFalse(q.is_correctly_answered([wrong.pk], ""))
        self.assertFalse(q.is_correctly_answered([], ""))

    def test_multiple_choice_requires_exact_set(self):
        exam = make_exam()
        q = Question.objects.create(exam=exam, text="Pick primes", kind=Question.Kind.MULTIPLE)
        a = Choice.objects.create(question=q, text="2", is_correct=True)
        b = Choice.objects.create(question=q, text="3", is_correct=True)
        c = Choice.objects.create(question=q, text="4", is_correct=False)
        self.assertTrue(q.is_correctly_answered([a.pk, b.pk], ""))
        self.assertFalse(q.is_correctly_answered([a.pk], ""))
        self.assertFalse(q.is_correctly_answered([a.pk, b.pk, c.pk], ""))

    def test_text_grading_is_case_insensitive(self):
        exam = make_exam()
        q = Question.objects.create(
            exam=exam,
            text="Capital of France?",
            kind=Question.Kind.TEXT,
            expected_text="Paris",
        )
        self.assertTrue(q.is_correctly_answered([], "  paris "))
        self.assertFalse(q.is_correctly_answered([], "London"))


class ViewTests(TestCase):
    def setUp(self):
        self.exam = make_exam()
        self.question = make_single_question(self.exam)
        self.correct = self.question.choices.get(is_correct=True)
        User = get_user_model()
        self.user = User.objects.create_user("student", password="pass12345")
        self.other = User.objects.create_user("other", password="pass12345")

    def test_list_shows_published_only(self):
        make_exam(title="Secret Exam", is_published=False)
        resp = self.client.get(reverse("exam-list"))
        self.assertContains(resp, "Algebra Basics")
        self.assertNotContains(resp, "Secret Exam")

    def test_take_exam_requires_login(self):
        resp = self.client.get(reverse("take-exam", args=[self.exam.slug]))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('take-exam', args=[self.exam.slug])}")

    def test_taking_exam_flow_grades_correctly(self):
        self.client.login(username="student", password="pass12345")
        resp = self.client.get(reverse("take-exam", args=[self.exam.slug]))
        self.assertEqual(resp.status_code, 200)
        attempt = Attempt.objects.get(user=self.user, exam=self.exam)
        self.assertEqual(attempt.max_score, 2)

        resp = self.client.post(
            reverse("submit-exam", args=[self.exam.slug]),
            {f"q{self.question.pk}": str(self.correct.pk)},
        )
        attempt.refresh_from_db()
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.score, 2)
        self.assertRedirects(resp, reverse("exam-result", args=[attempt.pk]))

        resp = self.client.get(reverse("exam-result", args=[attempt.pk]))
        self.assertContains(resp, "2 / 2")

    def test_wrong_answer_scores_zero(self):
        self.client.login(username="student", password="pass12345")
        self.client.get(reverse("take-exam", args=[self.exam.slug]))
        wrong = self.question.choices.get(text="3")
        self.client.post(
            reverse("submit-exam", args=[self.exam.slug]),
            {f"q{self.question.pk}": str(wrong.pk)},
        )
        attempt = Attempt.objects.get(user=self.user, exam=self.exam)
        self.assertEqual(attempt.score, 0)

    def test_cannot_view_others_result(self):
        attempt = Attempt.objects.create(user=self.other, exam=self.exam, completed_at="2026-01-01T00:00:00Z", score=1, max_score=2)
        self.client.login(username="student", password="pass12345")
        resp = self.client.get(reverse("exam-result", args=[attempt.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_refresh_keeps_single_attempt(self):
        self.client.login(username="student", password="pass12345")
        self.client.get(reverse("take-exam", args=[self.exam.slug]))
        self.client.get(reverse("take-exam", args=[self.exam.slug]))
        self.assertEqual(
            Attempt.objects.filter(user=self.user, exam=self.exam).count(), 1
        )

    def test_my_attempts_page(self):
        self.client.login(username="student", password="pass12345")
        resp = self.client.get(reverse("my-attempts"))
        self.assertEqual(resp.status_code, 200)
