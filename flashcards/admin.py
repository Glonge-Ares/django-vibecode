from django.contrib import admin

from .models import Card, Deck, DeckResult


class CardInline(admin.TabularInline):
    model = Card
    extra = 3
    ordering = ["position", "id"]


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "card_count", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CardInline]

    @admin.display(description="cards")
    def card_count(self, obj):
        return obj.cards.count()


@admin.register(DeckResult)
class DeckResultAdmin(admin.ModelAdmin):
    list_display = ("user", "deck", "known_count", "missed_count", "created_at")
    list_filter = ("deck",)
    search_fields = ("user__username", "deck__title")
    readonly_fields = ("created_at",)
