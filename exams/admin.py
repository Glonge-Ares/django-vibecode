from django.contrib import admin

from .models import Answer, Attempt, Choice, Exam, Question


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("exam", "kind", "points", "order", "text")
    list_filter = ("kind", "exam")
    inlines = [ChoiceInline]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    ordering = ["order", "id"]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "duration_minutes", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [QuestionInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "exam", "score", "max_score", "started_at", "completed_at")
    list_filter = ("exam", "expired")
    search_fields = ("user__username", "exam__title")
    readonly_fields = ("started_at", "completed_at", "score", "max_score")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "is_correct", "text_answer")
    list_filter = ("is_correct",)
