from django.urls import path

from . import views

urlpatterns = [
    path("", views.exam_list, name="exam-list"),
    path("exam/<slug:slug>/", views.exam_start, name="exam-start"),
    path("exam/<slug:slug>/take/", views.take_exam, name="take-exam"),
    path("exam/<slug:slug>/submit/", views.submit_exam, name="submit-exam"),
    path("attempts/<int:pk>/", views.exam_result, name="exam-result"),
    path("attempts/", views.my_attempts, name="my-attempts"),
]
