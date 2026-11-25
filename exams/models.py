from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Exam(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(
        default=0, help_text="0 means no time limit"
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "exam"
            slug, n = base, 1
            while Exam.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("exam-start", args=[self.slug])

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    class Kind(models.TextChoices):
        SINGLE = "single", "Single choice"
        MULTIPLE = "multiple", "Multiple choice"
        TEXT = "text", "Short text answer"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.SINGLE)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    expected_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Expected answer for short text questions (case-insensitive)",
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.exam.title}: {self.text[:60]}"

    @property
    def correct_choices(self):
        return set(self.choices.filter(is_correct=True).values_list("id", flat=True))

    @property
    def correct_text(self):
        return self.expected_text.strip().casefold()

    def is_correctly_answered(self, selected_ids, text_answer):
        if self.kind == self.Kind.TEXT:
            return (
                bool(self.correct_text)
                and text_answer.strip().casefold() == self.correct_text
            )
        selected = {int(pk) for pk in selected_ids}
        return bool(selected) and selected == self.correct_choices


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text


class Attempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts"
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    expired = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} - {self.exam.title} ({self.score}/{self.max_score})"

    @property
    def is_completed(self):
        return self.completed_at is not None

    @property
    def percentage(self):
        if not self.max_score:
            return 0.0
        return round(100 * self.score / self.max_score, 1)

    @property
    def passed(self):
        return self.is_completed and self.percentage >= 100 * settings.PASS_THRESHOLD


class Answer(models.Model):
    attempt = models.ForeignKey(
        Attempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choices = models.ManyToManyField(
        Choice, blank=True, related_name="answers"
    )
    text_answer = models.CharField(max_length=300, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        status = "correct" if self.is_correct else "wrong"
        return f"{self.attempt_id}/{self.question_id}: {status}"
