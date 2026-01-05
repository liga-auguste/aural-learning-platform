from django.urls import path
from .views import (
    HomeView,
    EntryListView, EntryDetailView,
    EntryCreateView, EntryUpdateView, EntryDeleteView,
    TermListView, entry_pk_redirect,
)

app_name = "modules"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    path("entries/", EntryListView.as_view(), name="entry_list"),
    path("entries/tag/<str:tag_slug>/", EntryListView.as_view(), name="entries_by_tag"),
    path("entries/new/", EntryCreateView.as_view(), name="entry_create"),

    path("entries/<int:pk>/", entry_pk_redirect, name="entry_detail_pk"),
    path("entries/<slug:slug>/", EntryDetailView.as_view(), name="entry_detail"),

    
    path("entries/<int:pk>/edit/", EntryUpdateView.as_view(), name="entry_update"),
    path("entries/<int:pk>/delete/", EntryDeleteView.as_view(), name="entry_delete"),

    path("terms/", TermListView.as_view(), name="term_list"),
]

