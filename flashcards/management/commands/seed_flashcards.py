from django.core.management.base import BaseCommand

from flashcards.models import Card, Deck

SEED = [
    {
        "title": "Django Terminology",
        "description": "Core concepts of the framework you are using right now.",
        "cards": [
            ("ORM", "Object-Relational Mapper: lets you query and modify database rows as Python objects."),
            ("Migration", "A versioned, ordered file that evolves the database schema without data loss."),
            ("View", "Python callable that takes an HttpRequest and returns an HttpResponse."),
            ("Template", "HTML file with special syntax for rendering dynamic content on the server."),
            ("Middleware", "Hook into Django's request/response pipeline, applied in settings order."),
            ("Slug", "URL-friendly label, usually ASCII and hyphenated, derived from a title."),
            ("CBV", "Class-Based View: a view implemented as a class with reusable mixins/generic logic."),
            ("Paginator", "Django utility that slices querysets into numbered pages."),
        ],
    },
    {
        "title": "PostgreSQL Essentials",
        "description": "Terms and concepts behind the database in this project.",
        "cards": [
            ("ACID", "Atomicity, Consistency, Isolation, Durability — guarantees of reliable transactions."),
            ("MVCC", "Multi-Version Concurrency Control: readers never block writers."),
            ("CTE", "Common Table Expression: a named temporary result set usable inside a query."),
            ("GIN index", "Generalized Inverted Index, optimized for containment queries (JSONB, arrays, full text)."),
            ("WAL", "Write-Ahead Log: durability mechanism that records changes before data pages."),
            ("VACUUM", "Maintenance process that reclaims storage and updates visibility maps."),
            ("SERIAL", "Pseudo-type for an auto-incrementing integer column backed by a sequence."),
            ("Foreign Key", "Constraint that enforces a reference to a referenced column in another table."),
        ],
    },
]


class Command(BaseCommand):
    help = "Create sample flashcard decks (idempotent, keyed by deck title)."

    def handle(self, *args, **options):
        for deck_data in SEED:
            cards_data = deck_data["cards"]
            deck, created = Deck.objects.get_or_create(
                title=deck_data["title"],
                defaults={"description": deck_data["description"]},
            )
            if not created:
                self.stdout.write(f"skip (exists): {deck.title}")
                continue
            for position, (term, definition) in enumerate(cards_data, start=1):
                Card.objects.create(
                    deck=deck, term=term, definition=definition, position=position
                )
            self.stdout.write(self.style.SUCCESS(f"created: {deck.title}"))
