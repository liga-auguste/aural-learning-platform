from django.urls import path
from .views import (
    HomeView,
    EntryListView, EntryDetailView,
    EntryCreateView, EntryUpdateView, EntryDeleteView,
)

app_name = "modules"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("entries/", EntryListView.as_view(), name="entry_list"),
    path("entries/tag/<str:tag_slug>/", EntryListView.as_view(), name="entries_by_tag"),
    path("entries/new/", EntryCreateView.as_view(), name="entry_create"),
    path("entries/<int:pk>/", EntryDetailView.as_view(), name="entry_detail"),
    path("entries/<int:pk>/edit/", EntryUpdateView.as_view(), name="entry_update"),
    path("entries/<int:pk>/delete/", EntryDeleteView.as_view(), name="entry_delete"),
]
