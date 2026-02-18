from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.contrib.auth import get_user_model
from django.utils.html import format_html

from .models import Module, GlossaryEntry, ModuleCompletion
from collections import defaultdict
from taggit.models import Tag
from .models import Aufgabentyp

try:
    admin.site.unregister(Tag)
except admin.sites.NotRegistered:
    pass

@admin.register(Aufgabentyp)
class AufgabentypAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")

# --- Glossar ---
@admin.register(GlossaryEntry)
class GlossaryEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "exam_relevant", "delete_link")
    list_filter = ("exam_relevant",)
    search_fields = ("title", "definition")
    prepopulated_fields = {"slug": ("title",)}

    @admin.display(description="Löschen")
    def delete_link(self, obj):
        url = reverse("admin:modules_glossaryentry_delete", args=[obj.pk])
        return format_html('<a class="deletelink" href="{}">Löschen</a>', url)

# --- Completions (statt admin.site.register(ModuleCompletion) "blank") ---
@admin.register(ModuleCompletion)
class ModuleCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "module", "completed_at")
    list_filter = ("user", "module")
    search_fields = ("user__username", "user__email", "module__title")
    ordering = ("-completed_at",)


# --- Module ---
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "title",
        # "has_completion",  # <- empfehle ich rauszunehmen (siehe Hinweis unten)
        "terms_list",
        "has_homework",
        "pdf_count",
        "audio_count",
        "slug",
    )

    # OPTIONAL: Wenn du es behalten willst, benenne es ehrlich:
    @admin.display(boolean=True, description="Hat mind. 1 Abschluss")
    def has_completion(self, obj):
        return ModuleCompletion.objects.filter(module=obj).exists()

    @admin.display(boolean=True, description="Hausaufgabe")
    def has_homework(self, obj):
        return bool(obj.homework and obj.homework.strip())

    @admin.display(description="PDFs")
    def pdf_count(self, obj):
        return sum(bool(getattr(obj, f"pdf_{i}")) for i in range(1, 5))

    @admin.display(description="Audio")
    def audio_count(self, obj):
        return sum(bool(getattr(obj, f"audio_{i}")) for i in range(1, 5))

    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order", "id")
    search_fields = ("title", "inclass", "homework", "terms__name")
    prepopulated_fields = {"slug": ("title",)}

    def terms_list(self, obj):
        return ", ".join(obj.terms.names())
    terms_list.short_description = "Begriffe"

    change_list_template = "admin/modules/module_change_list.html"
      
    # ---------- Matrix: Custom URLs ----------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "progress-matrix/",
                self.admin_site.admin_view(self.progress_matrix_view),
                name="modules_module_progress_matrix",
            ),
            path(
                "progress-matrix/toggle/<int:user_id>/<int:module_id>/",
                self.admin_site.admin_view(self.toggle_completion_view),
                name="modules_module_progress_toggle",
            ),
        ]
        return custom + urls

    def progress_matrix_view(self, request):
        User = get_user_model()

        users = list(User.objects.filter(is_staff=False).order_by("username"))
        modules = list(Module.objects.all().order_by("order", "id"))

        # user_id -> set(module_id)
        completed_map = defaultdict(set)
        for user_id, module_id in ModuleCompletion.objects.values_list("user_id", "module_id"):
            completed_map[user_id].add(module_id)

        rows = [{"user": u, "completed_ids": completed_map.get(u.id, set())} for u in users]

        ctx = dict(
        self.admin_site.each_context(request),
        title="Modul-Fortschritt der Benutzer",
        rows=rows,
        modules=modules,
        )
        return TemplateResponse(request, "admin/modules/progress_matrix.html", ctx)

    def toggle_completion_view(self, request, user_id, module_id):
        if request.method != "POST":
            return redirect(reverse("admin:modules_module_progress_matrix"))

        obj, created = ModuleCompletion.objects.get_or_create(
            user_id=user_id,
            module_id=module_id,
        )
    
        if not created:
            obj.delete()

        return redirect(reverse("admin:modules_module_progress_matrix"))
