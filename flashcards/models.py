from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Deck(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "deck"
            slug, n = base, 1
            while Deck.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("deck-detail", args=[self.slug])


class Card(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cards")
    term = models.CharField(max_length=200)
    definition = models.TextField()
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.deck.title}: {self.term}"


class DeckResult(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="results")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deck_results"
    )
    known_count = models.PositiveIntegerField(default=0)
    missed_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.deck.title}: {self.known_count}/{self.total}"

    @property
    def total(self):
        return self.known_count + self.missed_count

    @property
    def percentage(self):
        if not self.total:
            return 0.0
        return round(100 * self.known_count / self.total, 1)

    @property
    def passed(self):
        return self.percentage >= 100 * settings.PASS_THRESHOLD
