from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, DetailView,
    CreateView, UpdateView, DeleteView,
)
from .models import Module
from .forms import ModuleForm


class HomeView(TemplateView):
    template_name = "modules/home.html"


class LockedView(LoginRequiredMixin):
    login_url = "login"


class EntryListView(LockedView, ListView):
    model = Module
    template_name = "modules/entry_list.html"
    context_object_name = "object_list"
    
    def get_queryset(self):
        return (
            Module.objects
            .all()
            .prefetch_related("terms")      # wichtig für taggit
            .order_by("order", "id")
        )


class EntryDetailView(LockedView, DetailView):
    model = Module
    template_name = "modules/entry_detail.html"


class EntryCreateView(LockedView, SuccessMessageMixin, CreateView):
    model = Module
    template_name = "modules/entry_form.html"
    fields = ["title", "inclass", "homework", "terms", "pdf_1", "pdf_2", "pdf_3", "pdf_4"]
    success_url = reverse_lazy("entry_list")
    success_message = "Das Modul wurde erstellt!"


class EntryUpdateView(LockedView, SuccessMessageMixin, UpdateView):
    model = Module
    template_name = "modules/entry_form.html"
    fields = ["title", "inclass", "homework", "terms", "pdf_1", "pdf_2", "pdf_3", "pdf_4"]
    success_message = "Das Modul wurde aktualisiert!"

    def get_success_url(self):
        return reverse_lazy("entry_detail", kwargs={"pk": self.object.pk})


class EntryDeleteView(LockedView, SuccessMessageMixin, DeleteView):
    model = Module
    template_name = "modules/entry_confirm_delete.html"
    success_url = reverse_lazy("entry_list")
    success_message = "Das Modul wurde gelöscht!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class ModuleCreateView(CreateView):
    model = Module
    form_class = ModuleForm
