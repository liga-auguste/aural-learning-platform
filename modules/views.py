from django.db.models import Max
from django.db.models import Q
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

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import ContactForm
from entries.models import Entry

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
            .prefetch_related("terms")
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
            return qs.filter(terms__in=[qs_tag])
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        if obj.order is None:
            context["prev_entry"] = None
            context["next_entry"] = None
            return context

        context["prev_entry"] = (
            Module.objects
            .filter(
                Q(order__lt=obj.order) |
                Q(order=obj.order, id__lt=obj.id)
            )
            .order_by("-order", "-id")
            .first()
        )

        context["next_entry"] = (
            Module.objects
            .filter(
                Q(order__gt=obj.order) |
                Q(order=obj.order, id__gt=obj.id)
            )
            .order_by("order", "id")
            .first()
        )

        return context


class EntryCreateView(LockedView, SuccessMessageMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = "modules/entry_form.html"
    success_url = reverse_lazy("modules:entry_list")
    success_message = "Das Modul wurde erstellt!"

class EntryUpdateView(LockedView, SuccessMessageMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = "modules/entry_form.html"
    success_message = "Das Modul wurde aktualisiert!"

    def get_success_url(self):
        return reverse_lazy("modules:entry_detail", kwargs={"pk": self.object.pk})


class EntryDeleteView(LockedView, SuccessMessageMixin, DeleteView):
    model = Module
    template_name = "modules/entry_confirm_delete.html"
    success_url = reverse_lazy("modules:entry_list")
    success_message = "Das Modul wurde gelöscht!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            subject = form.cleaned_data.get("subject") or "Kontaktformular"
            message = form.cleaned_data["message"]

            body = f"Von: {name} <{email}>\n\nNachricht:\n{message}"

            # E-Mail senden (fürs Portfolio reicht die Console-Variante, s. Settings)
            send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[getattr(settings, "CONTACT_RECIPIENT", "ligaauguste@gmail.com")],
                fail_silently=True,  # im Portfolio okay
            )
            return redirect(reverse("contact_thanks"))
    else:
        form = ContactForm()
    return render(request, "contact.html", {"form": form})

class TermListView(ListView):
    model = Tag
    template_name = "entries/term_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        tags = Tag.objects.all().order_by("name")

        # jedem Tag die passenden Entries anhängen
        for tag in tags:
            tag.modules = Module.objects.filter(terms=tag).only("id", "title")

        return tags