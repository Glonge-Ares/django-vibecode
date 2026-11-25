from django.core.management.base import BaseCommand

from exams.models import Choice, Exam, Question

SEED = [
    {
        "title": "Python Fundamentals",
        "description": "Core Python: data types, control flow, functions and OOP basics.",
        "duration_minutes": 20,
        "questions": [
            {
                "text": "Which of these are mutable built-in types in Python?",
                "kind": "multiple",
                "points": 2,
                "choices": [("list", True), ("tuple", False), ("dict", True), ("str", False)],
            },
            {
                "text": "What does `len({'a': 1, 'b': 2})` return?",
                "kind": "single",
                "points": 1,
                "choices": [("1", False), ("2", True), ("4", False)],
            },
            {
                "text": "Which keyword defines a generator function?",
                "kind": "single",
                "points": 1,
                "choices": [("yield", True), ("generate", False), ("return", False), ("async", False)],
            },
            {
                "text": "What is the output of `type(10 / 3)`?",
                "kind": "single",
                "points": 1,
                "choices": [
                    ("<class 'int'>", False),
                    ("<class 'float'>", True),
                    ("<class 'complex'>", False),
                ],
            },
            {
                "text": "Which dunder method is called for string representation in the debugger (repr)?",
                "kind": "text",
                "points": 2,
                "expected_text": "__repr__",
            },
        ],
    },
    {
        "title": "Django Web Framework",
        "description": "ORM, URL routing, views, templates and the admin site.",
        "duration_minutes": 25,
        "questions": [
            {
                "text": "Which command applies unapplied migrations?",
                "kind": "single",
                "points": 1,
                "choices": [
                    ("python manage.py migrate", True),
                    ("python manage.py syncdb", False),
                    ("python manage.py makemigrations", False),
                    ("python manage.py deploy", False),
                ],
            },
            {
                "text": "Select everything that belongs to Django's request/response cycle.",
                "kind": "multiple",
                "points": 3,
                "choices": [
                    ("Middleware", True),
                    ("URL resolver", True),
                    ("Model mixin", False),
                    ("Template context", True),
                ],
            },
            {
                "text": "By default, `QuerySet` evaluation is what?",
                "kind": "single",
                "points": 1,
                "choices": [
                    ("Lazy", True),
                    ("Eager", False),
                    ("Cached forever", False),
                    ("Synchronous", False),
                ],
            },
            {
                "text": "Name the class-based view designed for creating objects.",
                "kind": "text",
                "points": 2,
                "expected_text": "CreateView",
            },
        ],
    },
    {
        "title": "SQL & PostgreSQL Basics",
        "description": "Queries, joins, aggregation and indexing in PostgreSQL.",
        "duration_minutes": 20,
        "questions": [
            {
                "text": "Which clause filters rows *after* aggregation?",
                "kind": "single",
                "points": 1,
                "choices": [("HAVING", True), ("WHERE", False), ("ORDER BY", False), ("ON", False)],
            },
            {
                "text": "Select all statements that are valid PostgreSQL constraint types.",
                "kind": "multiple",
                "points": 2,
                "choices": [
                    ("PRIMARY KEY", True),
                    ("FOREIGN KEY", True),
                    ("TRIGGER", False),
                    ("UNIQUE", True),
                ],
            },
            {
                "text": "What does `SELECT COUNT(*) FROM t;` return if `t` is empty?",
                "kind": "single",
                "points": 1,
                "choices": [("0", True), ("NULL", False), ("1", False), ("error", False)],
            },
            {
                "text": "Which index type is best for full-text search queries?",
                "kind": "text",
                "points": 2,
                "expected_text": "GIN",
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Create sample exams and questions (idempotent, keyed by exam title)."

    def handle(self, *args, **options):
        for exam_data in SEED:
            questions_data = exam_data.pop("questions")
            exam, created = Exam.objects.get_or_create(
                title=exam_data["title"],
                defaults={
                    "description": exam_data["description"],
                    "duration_minutes": exam_data["duration_minutes"],
                },
            )
            if not created:
                self.stdout.write(f"skip (exists): {exam.title}")
                exam_data["questions"] = questions_data
                continue

            for order, qdata in enumerate(questions_data, start=1):
                question = Question.objects.create(
                    exam=exam,
                    text=qdata["text"],
                    kind=qdata["kind"],
                    points=qdata["points"],
                    order=order,
                    expected_text=qdata.get("expected_text", ""),
                )
                for text, is_correct in qdata.get("choices", []):
                    Choice.objects.create(
                        question=question, text=text, is_correct=is_correct
                    )
            self.stdout.write(self.style.SUCCESS(f"created: {exam.title}"))
