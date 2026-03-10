from django.contrib import admin
from django import forms
from django.urls import path, reverse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Prefetch, Count

from .models import Aufgabentyp, Module, GlossaryEntry, ModuleCompletion, ProgressMatrixProxy, Unit, Submission, SubmissionFile
from collections import defaultdict

from adminsortable2.admin import SortableAdminMixin

@admin.register(Aufgabentyp)
class AufgabentypAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

# --- Glossar ---

@admin.register(GlossaryEntry)
class GlossaryEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "exam_relevant", "modules_count", "delete_link")
    list_editable = ("exam_relevant",)
    list_filter = ("exam_relevant",)
    search_fields = ("title", "definition")
    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(modules_count=Count("modules", distinct=True))

    @admin.display(description="Module", ordering="modules_count")
    def modules_count(self, obj):
        return obj.modules_count

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

class ModuleAdminForm(forms.ModelForm):
    tasktype = forms.ModelMultipleChoiceField(
        queryset=Aufgabentyp.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Aufgabentypen",
    )

    class Meta:
        model = Module
        fields = ("order", "title", "slug", "inclass", "homework", "tasktype",
          "pdf_1", "pdf_2", "pdf_3", "pdf_4", "audio_1", "audio_1_title", "audio_2", "audio_2_title", "audio_3", "audio_3_title", "audio_4", "audio_4_title")

# --- Module ---
@admin.register(Module)
class ModuleAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        "order",
        "title",
        # "has_completion",  # <- empfehle ich rauszunehmen (siehe Hinweis unten)
        "tasktype_list",
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

    list_display_links = ("title",)
    ordering = ("order", "id")
    search_fields = ("title", "inclass", "homework", "tasktype__name")
    prepopulated_fields = {"slug": ("title",)}
    
    form = ModuleAdminForm

    @admin.display(description="Aufgabentypen")
    def tasktype_list(self, obj):
        names = list(obj.tasktype.values_list("name", flat=True))
        return ", ".join(names) if names else "–"
    
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

@admin.register(ProgressMatrixProxy)
class ProgressMatrixProxyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse("admin:modules_module_progress_matrix"))

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("label", "date_only", "kind", "toggle_submissions")
    list_filter = ("kind", "submissions_enabled", ("date", admin.DateFieldListFilter))
    search_fields = ("title", "notes", "module__title")
    ordering = ("-date", "-id")
    autocomplete_fields = ("module",)
    date_hierarchy = "date"

    @admin.display(description="Einheit")
    def label(self, obj: Unit) -> str:
        if obj.module:
            order = getattr(obj.module, "order", None)
            title = (getattr(obj.module, "title", "") or "").strip()
            base = f"Modul {order}" if order is not None else "Modul"
            if title and title.lower() != base.lower():
                base = f"{base} – {title}"
            return base
        return obj.title or dict(obj.KIND_CHOICES).get(obj.kind, obj.kind)

    @admin.display(description="Datum")
    def date_only(self, obj: Unit) -> str:
        return timezone.localtime(obj.date).strftime("%Y-%m-%d")

    @admin.display(description="Abgaben")
    def toggle_submissions(self, obj: Unit):
        url = reverse("admin:modules_unit_toggle_submissions", args=[obj.pk])
        label = "🟢 Offen" if obj.submissions_enabled else "🔒 Gesperrt"
        return format_html('<a class="button" href="{}">{}</a>', url, label)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "toggle-submissions/<int:unit_id>/",
                self.admin_site.admin_view(self.toggle_submissions_view),
                name="modules_unit_toggle_submissions",
            ),
        ]
        return custom + urls

    def toggle_submissions_view(self, request, unit_id):
        unit = Unit.objects.get(pk=unit_id)
        unit.submissions_enabled = not unit.submissions_enabled
        unit.save(update_fields=["submissions_enabled"])
        return redirect(request.META.get("HTTP_REFERER", "admin:index"))


class SubmissionFileInline(admin.TabularInline):
    model = SubmissionFile
    extra = 0
    fields = ("display_name", "file", "position", "uploaded_at")
    readonly_fields = ("uploaded_at",)
    ordering = ("position", "uploaded_at", "id")

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    changelist_template = "admin/modules/submission/change_list.html"

    list_display = (
        "unit",
        "student",
        "status",
        "submitted_at",
        "updated_at",
        "files_count",
        "toggle_button",
    )

    list_filter = ("status", "unit__kind", ("unit__date", admin.DateFieldListFilter))
    search_fields = (
        "student__username",
        "student__email",
        "student__first_name",
        "student__last_name",
        "unit__module__title",
        "unit__title",
    )

    autocomplete_fields = ("unit", "student")
    ordering = ("-unit__date", "unit_id", "student__username", "-updated_at")

    inlines = [SubmissionFileInline]
    readonly_fields = ("submitted_at", "updated_at")

    actions = ("mark_submitted", "mark_corrected", "toggle_status")

    @admin.display(description="Dateien")
    def files_count(self, obj):
        return obj.files.count()

    @admin.display(description="Toggle")
    def toggle_button(self, obj):
        url = reverse("admin:modules_submission_toggle_status", args=[obj.pk])
        return format_html('<a class="button" href="{}">🔁</a>', url)

    @admin.action(description="Als eingereicht markieren")
    def mark_submitted(self, request, queryset):
        queryset.update(status=Submission.SUBMITTED)

    @admin.action(description="Als korrigiert markieren")
    def mark_corrected(self, request, queryset):
        queryset.update(status=Submission.CORRECTED)

    @admin.action(description="Status toggeln (Eingereicht ↔ Korrigiert)")
    def toggle_status(self, request, queryset):
        for obj in queryset:
            obj.status = (
                Submission.CORRECTED
                if obj.status == Submission.SUBMITTED
                else Submission.SUBMITTED
            )
            obj.save(update_fields=["status"])

    def toggle_status_view(self, request, submission_id):
        obj = Submission.objects.get(pk=submission_id)

        obj.status = (
            Submission.CORRECTED
            if obj.status == Submission.SUBMITTED
            else Submission.SUBMITTED
        )

        obj.save(update_fields=["status"])

        return redirect(request.META.get("HTTP_REFERER", "admin:index"))

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "toggle-status/<int:submission_id>/",
                self.admin_site.admin_view(self.toggle_status_view),
                name="modules_submission_toggle_status",
            ),
        ]
        return custom + urls