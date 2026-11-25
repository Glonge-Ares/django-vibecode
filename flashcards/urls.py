from django.urls import path

from . import views

urlpatterns = [
    path("", views.deck_list, name="deck-list"),
    path("deck/<slug:slug>/", views.deck_detail, name="deck-detail"),
    path("deck/<slug:slug>/study/", views.deck_study, name="deck-study"),
    path("deck/<slug:slug>/mark/", views.deck_study_mark, name="deck-mark"),
]
