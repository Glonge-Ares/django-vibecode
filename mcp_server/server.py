"""Custom MCP server for the ExamPrep project.

Exposes the PostgreSQL-backed exam data (via the Django ORM) to opencode
agents as MCP tools. Runs over stdio; register it in opencode.json.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DB_HOST", "127.0.0.1")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import connection  # noqa: E402
from django.db import models  # noqa: E402
from django.utils import timezone  # noqa: E402

from exams.models import Attempt, Exam  # noqa: E402

from mcp.server.mcpserver import MCPServer  # noqa: E402

mcp = MCPServer("exam-db")


@mcp.tool()
def list_exams(include_unpublished: bool = False) -> list[dict]:
    """List exams with question counts and attempt counts. Set
    include_unpublished=True to also see exams hidden from students."""
    qs = Exam.objects.all()
    if not include_unpublished:
        qs = qs.filter(is_published=True)
    return [
        {
            "slug": e.slug,
            "title": e.title,
            "is_published": e.is_published,
            "duration_minutes": e.duration_minutes,
            "questions": e.questions.count(),
            "total_points": e.total_points,
            "attempts": e.attempts.count(),
        }
        for e in qs
    ]


@mcp.tool()
def get_exam(slug: str) -> dict:
    """Get one exam by slug: metadata, totals and best attempt per user."""
    exam = Exam.objects.get(slug=slug)
    return {
        "slug": exam.slug,
        "title": exam.title,
        "description": exam.description,
        "is_published": exam.is_published,
        "duration_minutes": exam.duration_minutes,
        "question_count": exam.questions.count(),
        "total_points": exam.total_points,
        "created_at": exam.created_at.isoformat(),
        "attempts": [
            {
                "attempt_id": a.id,
                "user": a.user.username,
                "score": a.score,
                "max_score": a.max_score,
                "completed": a.is_completed,
                "expired": a.expired,
                "started_at": a.started_at.isoformat(),
            }
            for a in exam.attempts.select_related("user")[:20]
        ],
    }


@mcp.tool()
def list_questions(slug: str) -> list[dict]:
    """List every question of an exam with its choices, correct answers
    and expected short-text answers (full answer key)."""
    exam = Exam.objects.get(slug=slug)
    return [
        {
            "id": q.id,
            "order": q.order,
            "kind": q.kind,
            "points": q.points,
            "text": q.text,
            "choices": [
                {"id": c.id, "text": c.text, "is_correct": c.is_correct}
                for c in q.choices.all()
            ],
            "expected_text": q.expected_text,
        }
        for q in exam.questions.prefetch_related("choices")
    ]


@mcp.tool()
def exam_stats(slug: str) -> dict:
    """Aggregated statistics for an exam: completion rate, average score,
    pass rate (threshold from settings.EXAM_PASS_THRESHOLD)."""
    exam = Exam.objects.get(slug=slug)
    attempts = Attempt.objects.filter(exam=exam, completed_at__isnull=False)
    total = attempts.count()
    avg = attempts.aggregate(avg=models.Avg("score"))["avg"] or 0.0
    avg_max = attempts.aggregate(avg=models.Avg("max_score"))["avg"] or 0.0
    pass_pct = 0.0
    if total:
        passed = sum(1 for a in attempts if a.passed)
        pass_pct = round(100 * passed / total, 1)
    return {
        "slug": exam.slug,
        "title": exam.title,
        "completed_attempts": total,
        "in_progress_attempts": exam.attempts.filter(completed_at__isnull=True).count(),
        "average_score": round(float(avg), 2),
        "average_max_score": round(float(avg_max), 2),
        "pass_rate_percent": pass_pct,
    }


@mcp.tool()
def get_attempt(attempt_id: int) -> dict:
    """Get one attempt with all answers, selected choices and correctness."""
    attempt = Attempt.objects.select_related("user", "exam").get(pk=attempt_id)
    answers = []
    for a in attempt.answers.select_related("question").prefetch_related(
        "selected_choices", "question__choices"
    ):
        answers.append(
            {
                "question": a.question.text,
                "kind": a.question.kind,
                "is_correct": a.is_correct,
                "selected_choices": [c.text for c in a.selected_choices.all()],
                "text_answer": a.text_answer,
                "correct_choices": [
                    c.text for c in a.question.choices.filter(is_correct=True)
                ],
                "expected_text": a.question.expected_text,
            }
        )
    return {
        "attempt_id": attempt.id,
        "user": attempt.user.username,
        "exam": attempt.exam.title,
        "started_at": attempt.started_at.isoformat(),
        "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
        "score": attempt.score,
        "max_score": attempt.max_score,
        "percentage": attempt.percentage,
        "passed": attempt.passed,
        "expired": attempt.expired,
        "answers": answers,
    }


@mcp.tool()
def get_db_schema() -> list[dict]:
    """PostgreSQL schema of every table used by the app (columns, types,
    keys) — useful before writing raw SQL or checking migrations."""
    tables = []
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        for (table,) in cur.fetchall():
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s ORDER BY ordinal_position
                """
                ,
                [table],
            )
            columns = [
                {"name": c, "type": t, "nullable": n == "YES", "default": d}
                for c, t, n, d in cur.fetchall()
            ]
            tables.append({"table": table, "columns": columns})
    return tables


@mcp.tool()
def list_users() -> list[dict]:
    """List registered users with attempt counts (who studies what)."""
    User = get_user_model()
    return [
        {
            "username": u.username,
            "is_staff": u.is_staff,
            "date_joined": u.date_joined.isoformat(),
            "attempts": u.attempts.count(),
            "completed": u.attempts.filter(completed_at__isnull=False).count(),
        }
        for u in User.objects.all().order_by("username")
    ]


if __name__ == "__main__":
    mcp.run()
