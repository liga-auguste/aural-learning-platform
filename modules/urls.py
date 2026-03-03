from django.urls import path
from django.views.generic import RedirectView

from . import views
from .views import (
    EntryListView, EntryDetailView,
    EntryCreateView, EntryUpdateView, EntryDeleteView,
    GlossaryListView,
    ExamRequirementsView,
    TaskTypeListView,
    StudentDashboardView,
    StudentSubmissionsListView, StudentSubmissionsDetailView,
    entry_pk_redirect,
    EntryToggleCompleteView,
)

app_name = "modules"

urlpatterns = [
    path("", views.RoleBasedHomeRedirectView.as_view(), name="home"),

    # NEU: echte Module-Routen
    path("modules/", EntryListView.as_view(), name="entry_list"),
    path("modules/tag/<str:tag_slug>/", EntryListView.as_view(), name="entries_by_tag"),
    path("modules/new/", EntryCreateView.as_view(), name="entry_create"),

    path("modules/<int:pk>/", entry_pk_redirect, name="entry_detail_pk"),
    path("modules/<slug:slug>/", EntryDetailView.as_view(), name="entry_detail"),

    path("modules/<int:pk>/edit/", EntryUpdateView.as_view(), name="entry_update"),
    path("modules/<int:pk>/delete/", EntryDeleteView.as_view(), name="entry_delete"),

    path("modules/<slug:slug>/toggle-complete/",
         EntryToggleCompleteView.as_view(),
         name="entry_toggle_complete"),

    # ALT → NEU Redirects
    path("entries/", RedirectView.as_view(url="/modules/", permanent=True)),
    path("entries/new/", RedirectView.as_view(url="/modules/new/", permanent=True)),
    path("entries/tag/<str:tag_slug>/", RedirectView.as_view(url="/modules/tag/%(tag_slug)s/", permanent=True)),
    path("entries/<int:pk>/", RedirectView.as_view(url="/modules/%(pk)s/", permanent=True)),
    path("entries/<int:pk>/edit/", RedirectView.as_view(url="/modules/%(pk)s/edit/", permanent=True)),
    path("entries/<int:pk>/delete/", RedirectView.as_view(url="/modules/%(pk)s/delete/", permanent=True)),
    path("entries/<slug:slug>/toggle-complete/", RedirectView.as_view(url="/modules/%(slug)s/toggle-complete/", permanent=True)),
    path("entries/<slug:slug>/", RedirectView.as_view(url="/modules/%(slug)s/", permanent=True)),

    # Rest
    path("tasktypes/", TaskTypeListView.as_view(), name="tasktype_list"),
    path("glossar/", GlossaryListView.as_view(), name="glossary_list"),
    path("pruefungsanforderungen/", ExamRequirementsView.as_view(), name="exam_requirements"),

    path("teacher/", views.TeacherDashboardView.as_view(), name="teacher_dashboard"),
    path("teacher/students/", views.TeacherStudentListView.as_view(), name="teacher_student_list"),
    path("teacher/students/<int:pk>/", views.TeacherStudentDetailView.as_view(), name="teacher_student_detail"),
    path("teacher/students/<int:pk>/modules/<slug:slug>/toggle/", views.TeacherToggleCompletionView.as_view(), name="teacher_toggle_completion"),
    
    path("units/<int:unit_id>/upload/", views.upload_submission_file, name="upload_submission_file"),
    path("submission-files/<int:file_id>/delete/", views.delete_submission_file, name="delete_submission_file"),
    path("teacher/submissions/", views.TeacherSubmissionsDashboardView.as_view(), name="teacher_submissions_dashboard",),
    path("teacher/units/<int:pk>/toggle-submissions/", views.TeacherToggleUnitSubmissionsView.as_view(), name="teacher_toggle_unit_submissions",),
    path("teacher/units/<int:pk>/downloads/", views.SubmissionsDownloadView.as_view(), name="teacher_unit_submissions_downloads",),
    path("student/", StudentDashboardView.as_view(), name="student_dashboard"),
    path("student/submissions/", StudentSubmissionsListView.as_view(), name="student_submissions_list"),
    path("student/submissions/<int:pk>/", StudentSubmissionsDetailView.as_view(), name="student_submission_detail",),
    # path( "teacher/units/<int:pk>/submissions/", views.TeacherUnitSubmissionsView.as_view(), name="teacher_unit_submissions",),
]
