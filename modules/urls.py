from django.urls import path
from .views import (
    HomeView,
    EntryListView, EntryDetailView,
    EntryCreateView, EntryUpdateView, EntryDeleteView,
    TermListView, GlossaryListView, entry_pk_redirect, EntryToggleCompleteView,ExamRequirementsView,
)

from . import views

app_name = "modules"

urlpatterns = [
    path("", views.RoleBasedHomeRedirectView.as_view(), name="home"),

    path("entries/", EntryListView.as_view(), name="entry_list"),
    path("entries/tag/<str:tag_slug>/", EntryListView.as_view(), name="entries_by_tag"),
    path("entries/new/", EntryCreateView.as_view(), name="entry_create"),

    path("entries/<int:pk>/", entry_pk_redirect, name="entry_detail_pk"),
    path("entries/<slug:slug>/", EntryDetailView.as_view(), name="entry_detail"),

    
    path("entries/<int:pk>/edit/", EntryUpdateView.as_view(), name="entry_update"),
    path("entries/<int:pk>/delete/", EntryDeleteView.as_view(), name="entry_delete"),

    path("terms/", TermListView.as_view(), name="term_list"),
    path("glossar/", GlossaryListView.as_view(), name="glossary_list"),
    path("entries/<slug:slug>/toggle-complete/", EntryToggleCompleteView.as_view(), name="entry_toggle_complete"),
    path("pruefungsanforderungen/", ExamRequirementsView.as_view(), name="exam_requirements",),
    path("teacher/students/", views.TeacherStudentListView.as_view(), name="teacher_student_list",),
    path("teacher/students/<int:pk>/", views.TeacherStudentDetailView.as_view(), name="teacher_student_detail",),
    path("teacher/students/<int:pk>/modules/<slug:slug>/toggle/", views.TeacherToggleCompletionView.as_view(), name="teacher_toggle_completion",),
    path("teacher/", views.TeacherDashboardView.as_view(), name="teacher_dashboard"),
]

