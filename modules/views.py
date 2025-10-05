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

from django.utils.text import slugify
from taggit.models import Tag



class HomeView(TemplateView):
    template_name = "modules/home.html"


class LockedView(LoginRequiredMixin):
    login_url = "login"


class EntryListView(LockedView, ListView):
    model = Module
    template_name = "modules/entry_list.html"
    context_object_name = "entry"

    def get_queryset(self):
        tag_value = self.kwargs.get("tag_slug")
        qs = (
            Module.objects
            .all()
            .prefetch_related("tags")
            .order_by("order", "id")
        )
        if not tag_value:
            return qs

        # 1) Versuch: als Slug
        qs_tag = Tag.objects.filter(slug=tag_value).first()
        # 2) Fallback: als Name (mit Umlauten)
        if not qs_tag:
            qs_tag = Tag.objects.filter(name=tag_value).first()
        # 3) Fallback: slugify(Name)
        if not qs_tag:
            qs_tag = Tag.objects.filter(slug=slugify(tag_value)).first()

        if qs_tag:
            return qs.filter(tags__in=[qs_tag])
        # Wenn nichts passt, leere Liste zurückgeben (oder alle, wenn du magst)
        return Module.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_value = self.kwargs.get("tag_slug")
        if tag_value:
            context["current_tag"] = (
                Tag.objects.filter(slug=tag_value).first()
                or Tag.objects.filter(name=tag_value).first()
                or Tag.objects.filter(slug=slugify(tag_value)).first()
            )
        return context


class EntryDetailView(LockedView, DetailView):
    model = Module
    template_name = "modules/entry_detail.html"
    context_object_name = "entry"


class EntryCreateView(LockedView, SuccessMessageMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = "modules/entry_form.html"
    success_url = reverse_lazy("entry_list")
    success_message = "Das Modul wurde erstellt!"

class EntryUpdateView(LockedView, SuccessMessageMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = "modules/entry_form.html"
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

