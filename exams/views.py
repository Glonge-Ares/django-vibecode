from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Answer, Attempt, Exam, Question


def exam_list(request):
    exams = (
        Exam.objects.filter(is_published=True)
        .annotate(question_count=Count("questions"))
        .order_by("title")
        .prefetch_related("questions")
    )
    entries = []
    for exam in exams:
        entry = {
            "exam": exam,
            "question_count": exam.question_count,
            "total_points": sum(q.points for q in exam.questions.all()),
            "last_attempt": None,
        }
        if request.user.is_authenticated:
            entry["last_attempt"] = (
                Attempt.objects.filter(user=request.user, exam=exam)
                .order_by("-started_at")
                .first()
            )
        entries.append(entry)
    return render(request, "exams/exam_list.html", {"entries": entries})


def _get_published_exam(slug):
    exam = get_object_or_404(Exam, slug=slug)
    if not exam.is_published:
        raise Http404
    return exam


def exam_start(request, slug):
    exam = _get_published_exam(slug)
    in_progress = False
    if request.user.is_authenticated:
        in_progress = Attempt.objects.filter(
            user=request.user, exam=exam, completed_at__isnull=True
        ).exists()
    return render(
        request,
        "exams/exam_start.html",
        {
            "exam": exam,
            "questions": exam.questions.all(),
            "total_points": exam.total_points,
            "in_progress": in_progress,
        },
    )


@login_required
def take_exam(request, slug):
    exam = _get_published_exam(slug)
    questions = list(exam.questions.all())
    if not questions:
        messages.warning(request, "This exam has no questions yet.")
        return redirect("exam-start", slug=exam.slug)

    attempt = (
        Attempt.objects.filter(user=request.user, exam=exam, completed_at__isnull=True)
        .order_by("-started_at")
        .first()
    )
    if attempt is None:
        attempt = Attempt.objects.create(
            user=request.user, exam=exam, max_score=exam.total_points
        )
        messages.info(request, "Timer started. Good luck!")

    remaining = _remaining_seconds(attempt, exam)
    if remaining is not None and remaining <= 0:
        return _grade(request, attempt, questions, expired=True)

    return render(
        request,
        "exams/take_exam.html",
        {
            "exam": exam,
            "questions": questions,
            "attempt": attempt,
            "remaining": remaining,
        },
    )


def _remaining_seconds(attempt, exam):
    if not exam.duration_minutes:
        return None
    deadline = attempt.started_at + timezone.timedelta(minutes=exam.duration_minutes)
    return max(0, int((deadline - timezone.now()).total_seconds()))


@require_POST
@login_required
def submit_exam(request, slug):
    exam = _get_published_exam(slug)
    attempt = get_object_or_404(
        Attempt, user=request.user, exam=exam, completed_at__isnull=True
    )
    questions = list(exam.questions.all())
    remaining = _remaining_seconds(attempt, exam)
    expired = remaining is not None and remaining <= 0
    return _grade(request, attempt, questions, expired=expired)


@transaction.atomic
def _grade(request, attempt, questions, expired=False):
    score = 0
    for question in questions:
        raw = request.POST.getlist(f"q{question.pk}")
        if question.kind == Question.Kind.TEXT:
            selected, text_answer = [], (raw[0] if raw else "")
        else:
            selected, text_answer = raw, ""
        correct = question.is_correctly_answered(selected, text_answer)
        answer = Answer.objects.create(
            attempt=attempt,
            question=question,
            text_answer=text_answer,
            is_correct=correct,
        )
        if selected:
            answer.selected_choices.set(selected)
        if correct:
            score += question.points

    attempt.score = score
    attempt.max_score = sum(q.points for q in questions)
    attempt.expired = expired
    attempt.completed_at = timezone.now()
    attempt.save()
    if expired:
        messages.warning(request, "Time is up — your exam was graded.")
    return redirect("exam-result", pk=attempt.pk)


@login_required
def exam_result(request, pk):
    attempt = get_object_or_404(Attempt, pk=pk, user=request.user)
    if not attempt.is_completed:
        return redirect("take-exam", slug=attempt.exam.slug)
    answers = attempt.answers.select_related("question").prefetch_related(
        "selected_choices", "question__choices"
    )
    return render(
        request,
        "exams/exam_result.html",
        {"attempt": attempt, "exam": attempt.exam, "answers": answers},
    )


@login_required
def my_attempts(request):
    attempts = Attempt.objects.filter(user=request.user).select_related("exam")
    return render(request, "exams/my_attempts.html", {"attempts": attempts})
