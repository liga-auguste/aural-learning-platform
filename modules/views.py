# =============================
# Django Core
# =============================
import io
import zipfile
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, Count
from django.http import HttpResponseForbidden, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import (
    TemplateView, ListView, DetailView,
    CreateView, UpdateView, DeleteView,
)
from datetime import timedelta

# =============================
# Local Apps
# =============================
from accounts.mixins import TeacherRequiredMixin, StudentRequiredMixin
from accounts.models import InviteToken
from accounts.forms import AcceptInviteForm
from .forms import ModuleForm, ContactForm
from .models import (
    Aufgabentyp,
    Module,
    GlossaryEntry,
    ModuleCompletion,
    Unit,
    Submission,
    SubmissionFile,
)

def entry_pk_redirect(request, pk):
    entry = get_object_or_404(Module, pk=pk)
    return redirect("modules:entry_detail", slug=entry.slug)


class HomeView(TemplateView):
    template_name = "modules/home.html"


class LockedView(LoginRequiredMixin):
    login_url = "login"


class EntryListView(LockedView, ListView):
    model = Module
    template_name = "modules/entry_list.html"
    context_object_name = "entries"

    def get_queryset(self):
        tag_value = self.kwargs.get("tag_slug")
        q = (self.request.GET.get("q") or "").strip()

        qs = (
            Module.objects
            .all()
            .prefetch_related("tasktype")
            .order_by("order", "id")
        )

        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(inclass__icontains=q) |
                Q(homework__icontains=q) |
                Q(tasktype__name__icontains=q)
            ).distinct()

        if not tag_value:
            return qs

        qs_tag = (
            Aufgabentyp.objects.filter(slug=tag_value).first()
            or Aufgabentyp.objects.filter(name=tag_value).first()
            or Aufgabentyp.objects.filter(slug=slugify(tag_value)).first()
        )

        if qs_tag:
            return qs.filter(tasktype=qs_tag).distinct()

        return Module.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Suchbegriff für Template (z.B. Input value / Anzeige)
        context["q"] = (self.request.GET.get("q") or "").strip()

        tag_value = self.kwargs.get("tag_slug")
        if tag_value:
            context["current_tag"] = (
                Aufgabentyp.objects.filter(slug=tag_value).first()
                or Aufgabentyp.objects.filter(name=tag_value).first()
                or Aufgabentyp.objects.filter(slug=slugify(tag_value)).first()
            )

        completed_ids = set(
            ModuleCompletion.objects.filter(user=self.request.user)
            .values_list("module_id", flat=True)
        )
        context["completed_ids"] = completed_ids

        return context

class EntryDetailView(LockedView, DetailView):
    model = Module
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "modules/entry_detail.html"
    context_object_name = "entry"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        if obj.order is None:
            context["prev_entry"] = None
            context["next_entry"] = None
        else:
            context["prev_entry"] = (
                Module.objects
                .filter(Q(order__lt=obj.order) | Q(order=obj.order, id__lt=obj.id))
                .order_by("-order", "-id")
                .first()
            )
            context["next_entry"] = (
                Module.objects
                .filter(Q(order__gt=obj.order) | Q(order=obj.order, id__gt=obj.id))
                .order_by("order", "id")
                .first()
            )

        context["is_completed"] = ModuleCompletion.objects.filter(
            user=self.request.user,
            module=obj,
        ).exists()

        unit = getattr(obj, "unit", None)
        context["unit"] = unit
        context["has_submission_files"] = (
            unit is not None and
            SubmissionFile.objects.filter(
                submission__unit=unit,
                file__endswith=".pdf"
            ).exists()
        )

        submission = None
        can_edit = False
        lock_at = None

        if unit and self.request.user.is_authenticated and getattr(self.request.user, "is_student", False):
            submission = Submission.objects.filter(
                unit=unit,
                student=self.request.user
            ).first()

            if submission:
                can_edit = submission.is_editable_by_student()
            else:
                can_edit = False

            lock_at = None

        context["submission"] = submission
        context["can_edit"] = can_edit
        context["lock_at"] = lock_at
        context["now"] = timezone.now()

        audio_blocks = []
        for i in range(1, 5):
            audio = getattr(obj, f"audio_{i}")
            if audio:
                audio_blocks.append({
                    "file": audio,
                    "title": getattr(obj, f"audio_{i}_title", ""),
                })
        context["audio_blocks"] = audio_blocks

        return context
    
class EntryToggleCompleteView(LockedView, View):
    def post(self, request, slug):
        module = get_object_or_404(Module, slug=slug)

        completion = ModuleCompletion.objects.filter(
            user=request.user,
            module=module
        ).first()

        if completion:
            # Bereits abgeschlossen → rückgängig machen
            completion.delete()
        else:
            # Noch nicht abgeschlossen → anlegen
            ModuleCompletion.objects.create(
                user=request.user,
                module=module
            )

        # Zurück zur vorherigen Seite (wenn ?next=... gesetzt ist)
        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)

        # Fallback: zur Übersicht
        return redirect("modules:entry_list")


class EntryCreateView(TeacherRequiredMixin, SuccessMessageMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = "modules/entry_form.html"
    success_url = reverse_lazy("modules:entry_list")
    success_message = "Das Modul wurde erstellt!"

class EntryUpdateView(TeacherRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = "modules/entry_form.html"
    success_message = "Das Modul wurde aktualisiert!"

    def get_success_url(self):
        return reverse_lazy("modules:entry_detail", kwargs={"slug": self.object.slug})

class EntryDeleteView(TeacherRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Module
    template_name = "modules/entry_confirm_delete.html"
    success_url = reverse_lazy("modules:entry_list")
    success_message = "Das Modul wurde gelöscht!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

def contact_view(request):
    form = ContactForm()
    return render(request, "contact.html", {
        "form": form,
        "contact_email": settings.CONTACT_RECIPIENT,
    })

class TaskTypeListView(ListView):
    model = Aufgabentyp
    template_name = "modules/tasktype_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        return Aufgabentyp.objects.prefetch_related("modules").order_by("name")

class GlossaryListView(LockedView, ListView):
    model = GlossaryEntry
    template_name = "modules/glossary_list.html"
    context_object_name = "terms"

    def get_queryset(self):
        qs = (
            GlossaryEntry.objects
            .annotate(modules_count=Count("modules", distinct=True))
            .prefetch_related("modules")
        )

        # --- Filter ---
        filter_val = self.request.GET.get("filter", "all")
        if filter_val == "exam":
            qs = qs.filter(exam_relevant=True)
        elif filter_val == "non_exam":
            qs = qs.filter(exam_relevant=False)

        # --- Sort ---
        sort_val = self.request.GET.get("sort", "az")
        if sort_val == "count":
            qs = qs.order_by("-modules_count", "title")
        else:
            qs = qs.order_by("title")

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_filter"] = self.request.GET.get("filter", "all")
        ctx["current_sort"] = self.request.GET.get("sort", "az")
        counts = [t.modules_count for t in ctx["terms"]]
        max_count = max(counts, default=1) or 1
        ctx["max_count"] = max_count

        for term in ctx["terms"]:
            ratio = term.modules_count / max_count
            term.freq_pct = f"{int(ratio * 30)}%"

        ctx["exam_terms"]     = [t for t in ctx["terms"] if t.exam_relevant]
        ctx["non_exam_terms"] = [t for t in ctx["terms"] if not t.exam_relevant]

        # Stats (immer ungefiltert)
        all_annotated = GlossaryEntry.objects.annotate(mc=Count("modules", distinct=True))
        ctx["stats_total"] = all_annotated.count()
        ctx["stats_exam"] = all_annotated.filter(exam_relevant=True).count()
        ctx["stats_without_module"] = all_annotated.filter(mc=0).count()
        ctx["stats_shown"] = len(ctx["terms"])

        return ctx

@login_required
@require_POST
def glossary_toggle_exam(request, pk):
    if not getattr(request.user, "is_teacher", False):
        return HttpResponseForbidden("Nur Lehrkräfte.")

    term = get_object_or_404(GlossaryEntry, pk=pk)
    term.exam_relevant = not term.exam_relevant
    term.save(update_fields=["exam_relevant"])

    return redirect(request.POST.get("next", "/glossar/"))

class ExamRequirementsView(TemplateView):
    template_name = "modules/exam_requirements.html"
    
class TeacherStudentListView(TeacherRequiredMixin, ListView):
    template_name = "modules/teacher_student_list.html"
    context_object_name = "students"

    def get_queryset(self):
        User = get_user_model()
        return User.objects.filter(role=User.STUDENT).order_by("username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_modules = Module.objects.count()
        total_units = Unit.objects.count()
        total_enabled_units = Unit.objects.filter(submissions_enabled=True).count()

        teacher_modules = ModuleCompletion.objects.filter(
            user=self.request.user
        ).count()
        teacher_pct = round((teacher_modules / total_modules) * 100) if total_modules else 0

        completed_counts = {
            row["user_id"]: row["c"]
            for row in ModuleCompletion.objects.values("user_id").annotate(c=Count("id"))
        }

        submission_stats = {
            row["student_id"]: row
            for row in Submission.objects.values("student_id").annotate(
                total=Count("id"),
                corrected=Count("id", filter=Q(status=Submission.CORRECTED)),
            )
        }

        students_data = []
        for s in context["students"]:
            comp = completed_counts.get(s.id, 0)
            sub = submission_stats.get(s.id, {})
            hw_total = sub.get("total", 0)
            hw_corrected = sub.get("corrected", 0)
            hw_waiting = hw_total - hw_corrected
            hw_open = max(0, total_enabled_units - hw_total)
            progress_pct = round((comp / total_modules) * 100) if total_modules else 0
            students_data.append({
                "student": s,
                "completed": comp,
                "progress_pct": min(100, progress_pct),
                "hw_open": hw_open,
                "hw_waiting": hw_waiting,
                "hw_corrected": hw_corrected,
            })

        context["total_modules"] = total_modules
        context["total_units"] = total_units
        context["total_enabled_units"] = total_enabled_units
        context["teacher_modules"] = teacher_modules
        context["teacher_pct"] = teacher_pct
        context["students_data"] = students_data

        return context

class TeacherStudentDetailView(TeacherRequiredMixin, TemplateView):
    template_name = "modules/teacher_student_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        User = get_user_model()

        student = get_object_or_404(User, pk=self.kwargs["pk"], role=User.STUDENT)

        modules = Module.objects.order_by("order", "id").select_related("unit")

        completed_ids = set(
            ModuleCompletion.objects.filter(user=student).values_list("module_id", flat=True)
        )

        submissions_map = {
            sub.unit_id: sub
            for sub in Submission.objects.filter(student=student).select_related("unit")
        }

        module_rows = []
        for m in modules:
            unit = getattr(m, "unit", None)
            submission = submissions_map.get(unit.id) if unit else None
            module_rows.append({
                "module": m,
                "completed": m.id in completed_ids,
                "unit": unit,
                "submission": submission,
            })

        total_modules = len(module_rows)
        completed_count = len(completed_ids)
        progress_pct = round((completed_count / total_modules) * 100) if total_modules else 0
        hw_corrected = sum(1 for s in submissions_map.values() if s.status == Submission.CORRECTED)
        hw_submitted = len(submissions_map) - hw_corrected

        context["student"] = student
        context["module_rows"] = module_rows
        context["total_modules"] = total_modules
        context["completed_count"] = completed_count
        context["progress_pct"] = min(100, progress_pct)
        context["hw_submitted"] = hw_submitted
        context["hw_corrected"] = hw_corrected

        return context
    
class TeacherToggleCompletionView(TeacherRequiredMixin, View):
    def post(self, request, pk, slug):
        User = get_user_model()

        student = get_object_or_404(User, pk=pk, role=User.STUDENT)
        module = get_object_or_404(Module, slug=slug)

        completion = ModuleCompletion.objects.filter(
            user=student,
            module=module
        ).first()

        if completion:
            completion.delete()
        else:
            ModuleCompletion.objects.create(user=student, module=module)

        return redirect("modules:teacher_student_detail", pk=student.pk)

class TeacherDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = "modules/teacher_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        User = get_user_model()

        # -----------------------------
        # 1️⃣ Kursfortschritt (Module)
        # -----------------------------
        teacher_completed_modules_count = ModuleCompletion.objects.filter(
            user=self.request.user
        ).count()

        teacher_target = settings.COURSE_TARGET_MODULES
        teacher_progress_percent = (
            round((teacher_completed_modules_count / teacher_target) * 100)
            if teacher_target
            else 0
        )
        teacher_progress_percent = min(100, teacher_progress_percent)

        context["teacher_completed_modules_count"] = teacher_completed_modules_count
        context["teacher_target"] = teacher_target
        context["teacher_progress_percent"] = teacher_progress_percent

        # -----------------------------
        # 2️⃣ Dashboard-KPIs
        # -----------------------------
        context["student_count"] = User.objects.filter(role=User.STUDENT).count()
        context["module_count"] = Module.objects.count()

        # ✅ Variante A: "Zu korrigieren" (alle offenen Einreichungen)
        pending_qs = Submission.objects.filter(status=Submission.SUBMITTED)

        context["pending_submissions_count"] = pending_qs.count()
        context["pending_students_count"] = pending_qs.values("student").distinct().count()

        # -----------------------------
        # 3️⃣ Aktive Einheit (Organisation, nicht Fortschritt)
        # -----------------------------
        active_unit = (
            Unit.objects.filter(submissions_enabled=True)
            .select_related("module")
            .order_by("date", "number", "id")
            .first()
        )

        context["active_unit"] = active_unit
        context["active_module"] = active_unit.module if active_unit else None

        return context

class StudentDashboardView(StudentRequiredMixin, TemplateView):
    template_name = "modules/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user

        completed_ids = ModuleCompletion.objects.filter(
            user=self.request.user
        ).values_list("module_id", flat=True)

        next_module = (
            Module.objects
            .exclude(id__in=completed_ids)
            .order_by("order", "id")
            .first()
        )

        total_modules = Module.objects.count()

        completed_count = ModuleCompletion.objects.filter(
            user=self.request.user
        ).count()

        window_size = 10
        
        all_modules = list(
            Module.objects.order_by("order", "id")
        )

        start_index = 0

        if next_module:
            for i, module in enumerate(all_modules):
                if module.id == next_module.id:
                    start_index = i
                    break

        window_modules = all_modules[start_index:start_index + window_size]


        window_completed_count = sum(
            1 for m in window_modules if m.id in completed_ids
        )

        window_total = len(window_modules)
        window_open_count = window_total - window_completed_count
        
        context["window_total"] = window_total
        context["window_completed_count"] = window_completed_count
        context["window_open_count"] = window_open_count
        
        course_target = settings.COURSE_TARGET_MODULES
        course_progress_percent = min(100, round((completed_count / course_target) * 100))

        context["total_modules"] = total_modules
        context["completed_count"] = completed_count
        context["next_module"] = next_module
        context["course_target"] = course_target
        context["course_progress_percent"] = course_progress_percent

        return context
        

class RoleBasedHomeRedirectView(View):
    def get(self, request):

        # 1️⃣ Nicht eingeloggt → Login
        if not request.user.is_authenticated:
            return redirect("login")

        # 2️⃣ Lehrer
        if getattr(request.user, "is_teacher", False):
            return redirect("modules:teacher_dashboard")

        # 3️⃣ Schüler
        if getattr(request.user, "is_student", False):
            return redirect("modules:student_dashboard")

        # 4️⃣ Fallback (falls es weitere Rollen gibt)
        return redirect("modules:entry_list")

@login_required
@require_POST
def upload_submission_file(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)

    if not getattr(request.user, "is_student", False):
        return HttpResponseForbidden("Nur Schüler dürfen Dateien hochladen.")

    files = request.FILES.getlist("files")
    if not files:
        messages.warning(request, "Bitte wähle mindestens eine Datei aus.")
        if unit.module:
            return redirect("modules:entry_detail", slug=unit.module.slug)
        return redirect("modules:entry_list")

    if not unit.submissions_enabled:
        return HttpResponseForbidden("Uploads sind gesperrt.")
    
    submission, _ = Submission.objects.get_or_create(
        unit=unit,
        student=request.user,
    )

    if not submission.is_editable_by_student():
        return HttpResponseForbidden("Uploads sind gesperrt.")

    for f in files:
        SubmissionFile.objects.create(submission=submission, file=f)

    if unit.module:
        return redirect("modules:entry_detail", slug=unit.module.slug)
    return redirect("modules:entry_list")

@login_required
@require_POST
def delete_submission_file(request, file_id):
    sf = get_object_or_404(SubmissionFile, pk=file_id)
    submission = sf.submission

    # 1) Nur Schüler
    if not getattr(request.user, "is_student", False):
        return HttpResponseForbidden("Nur Schüler dürfen Dateien löschen.")

    # 2) Nur eigene Submission
    if submission.student_id != request.user.id:
        return HttpResponseForbidden("Keine Berechtigung.")

    # 3) Lock-Regel
    if not submission.is_editable_by_student():
        return HttpResponseForbidden("Löschen ist gesperrt (36h vor nächstem Unterricht).")

    slug = submission.unit.module.slug if submission.unit.module else None

    sf.delete()

# ✅ Wenn das die letzte Datei war, auch die leere Submission entfernen
    if not submission.files.exists():
        submission.delete()
    
    if slug:
        return redirect("modules:entry_detail", slug=slug)
    return redirect("modules:entry_list")

class TeacherToggleUnitSubmissionsView(TeacherRequiredMixin, View):
    def post(self, request, pk):
        unit = get_object_or_404(Unit, pk=pk)

        unit.submissions_enabled = not unit.submissions_enabled
        unit.save(update_fields=["submissions_enabled"])

        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)

        return redirect("modules:teacher_dashboard")

class TeacherSubmissionsDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = "modules/teacher_submissions_dash.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        User = get_user_model()

        # ✅ 1) Alle Schüler laden (damit auch "keine Abgabe" sichtbar ist)
        students = list(User.objects.filter(role=User.STUDENT).order_by("username", "id"))
        context["student_count"] = len(students)

        # ✅ 2) Units + Submissions + Files effizient laden
        units = (
            Unit.objects
            .select_related("module")
            .prefetch_related("submissions__student", "submissions__files")
            .annotate(
                submissions_count=Count("submissions", distinct=True),
                files_count=Count("submissions__files", distinct=True),

                uploaded_students_count=Count(
                    "submissions",
                    filter=Q(submissions__files__isnull=False),
                    distinct=True,
                ),
            )
            .order_by("number", "date", "id")
        )

        # ✅ 3) Pro Unit: student_rows bauen
        for u in units:
            subs_by_student_id = {s.student_id: s for s in u.submissions.all()}

            rows = []
            for student in students:
                sub = subs_by_student_id.get(student.id)

                if sub:
                    files = list(sub.files.all())
                    has_files = len(files) > 0

                    display_status = sub.status if has_files else None

                    rows.append({
                        "student_name": getattr(student, "username", str(student)),
                        "submission_id": sub.id,
                        "status": display_status,   # ✅ nur wenn has_files
                        "files": [{"url": f.file.url} for f in files],
                        "first_file_url": files[0].file.url if has_files else None,
})
                else:
                    rows.append({
                        "student_name": getattr(student, "username", str(student)),
                        "submission_id": None,
                        "status": None,
                        "files": [],
                        "first_file_url": None,
                    })

            u.student_rows = rows

        context["units"] = units
        context["total_units"] = units.count()
        context["enabled_units"] = units.filter(submissions_enabled=True).count()

        return context

@login_required
@require_POST
def teacher_mark_submission_corrected(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)

    # Teacher-only (du hast TeacherRequiredMixin nur für CBVs, hier: quick guard)
    if not getattr(request.user, "is_teacher", False):
        return HttpResponseForbidden("Nur Lehrkräfte.")

    # Nur wenn eingereicht -> korrigiert
    Submission.objects.filter(
        pk=submission.pk,
        status=Submission.SUBMITTED,
    ).update(status=Submission.CORRECTED)

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("modules:teacher_submissions_dashboard")


@login_required
@require_POST
def teacher_mark_unit_corrected(request, unit_id):
    unit = get_object_or_404(Unit, pk=unit_id)

    if not getattr(request.user, "is_teacher", False):
        return HttpResponseForbidden("Nur Lehrkräfte.")

    Submission.objects.filter(
        unit=unit,
        status=Submission.SUBMITTED,
    ).update(status=Submission.CORRECTED)

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("modules:teacher_submissions_dashboard")

class StudentSubmissionsListView(StudentRequiredMixin, TemplateView):
    template_name = "modules/student_submissions_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        # ------------------------------------------------------------
        # 1) Alle freigeschalteten Units (Hausaufgaben-relevant) holen
        # ------------------------------------------------------------
        enabled_units_qs = (
            Unit.objects
            .filter(submissions_enabled=True)
            .select_related("module")
            .order_by("date", "number", "id")
        )

        enabled_units = list(enabled_units_qs)

        # ------------------------------------------------------------
        # 2) Alle Submissions des Users für diese Units holen
        #    (inkl. Dateien, damit du in der Liste ggf. Downloads zeigen kannst)
        # ------------------------------------------------------------
        submissions_qs = (
            Submission.objects
            .filter(student=user, unit__in=enabled_units)
            .select_related("unit", "unit__module")
            .prefetch_related("files")
        )

        # Dictionary: unit_id -> submission
        submissions_by_unit_id = {s.unit_id: s for s in submissions_qs}

        # ------------------------------------------------------------
        # 3) "Nächste Unit nach Datum" vorberechnen (für 36h-Lock)
        #    Wir betrachten nur Units mit date != NULL.
        # ------------------------------------------------------------
        units_with_date = [u for u in enabled_units if getattr(u, "date", None)]
        units_with_date.sort(key=lambda u: u.date)

        # Map: unit_id -> lock_at (datetime) oder None
        lock_at_by_unit_id = {}

        for i, unit in enumerate(units_with_date):
            next_unit = units_with_date[i + 1] if i + 1 < len(units_with_date) else None
            if next_unit is None:
                lock_at_by_unit_id[unit.id] = None
            else:
                lock_at_by_unit_id[unit.id] = next_unit.date - timedelta(hours=36)

        # Units ohne date -> kein Lock (None)
        for unit in enabled_units:
            lock_at_by_unit_id.setdefault(unit.id, None)

        # ------------------------------------------------------------
        # 4) Zeilen bauen: pro Unit ein "Row"-Objekt mit Status + Links
        # ------------------------------------------------------------
        rows = []
        counts = {
            "enabled_units": len(enabled_units),
            "open": 0,
            "locked": 0,
            "submitted": 0,
            "corrected": 0,
        }

        for unit in enabled_units:
            submission = submissions_by_unit_id.get(unit.id)
            lock_at = lock_at_by_unit_id.get(unit.id)

            if submission:
                # Es gibt eine Submission: Status kommt aus Submission.status
                if submission.status == Submission.CORRECTED:
                    status_key = "corrected"
                else:
                    status_key = "submitted"
            else:
                # Keine Submission vorhanden -> offen oder gesperrt
                if lock_at is not None and now >= lock_at:
                    status_key = "locked"
                else:
                    status_key = "open"

            counts[status_key] += 1

            rows.append({
                "unit": unit,
                "module": unit.module,
                "submission": submission,     # None wenn noch nicht abgegeben
                "status": status_key,         # open | locked | submitted | corrected
                "lock_at": lock_at,           # None wenn nicht berechenbar
            })

        # Optional: sortiere, wie du’s im UI willst (z.B. gesperrt zuerst)
        status_order = {"locked": 0, "open": 1, "submitted": 2, "corrected": 3}
        rows.sort(key=lambda r: (status_order.get(r["status"], 99),
                                 r["unit"].date is None,  # dated zuerst
                                 r["unit"].date or timezone.datetime.min.replace(tzinfo=timezone.get_current_timezone()),
                                 r["unit"].id))

        # ------------------------------------------------------------
        # 5) Context für Template + KPI-Kachel
        # ------------------------------------------------------------
        context["rows"] = rows
        context["counts"] = counts

        # Diese Keys sind praktisch fürs Dashboard-KPI (falls du sie hier wiederverwenden willst)
        context["homework_enabled_units_count"] = counts["enabled_units"]
        context["homework_open_count"] = counts["open"]
        context["homework_locked_count"] = counts["locked"]
        context["homework_submitted_count"] = counts["submitted"]
        context["homework_corrected_count"] = counts["corrected"]

        return context
    
class StudentSubmissionsDetailView(StudentRequiredMixin, DetailView):
    """
    Detailansicht einer Abgabe für Schüler:
    - zeigt nur die Abgabe des eingeloggten Schülers
    - inklusive Dateien (prefetch)
    """
    model = Submission
    template_name = "modules/student_submission_detail.html"
    context_object_name = "submission"

    def get_queryset(self):
        return (
            Submission.objects
            .filter(student=self.request.user)
            .select_related("unit", "unit__module")
            .prefetch_related("files")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        submission = self.object
        ctx["can_edit"] = submission.is_editable_by_student()
        ctx["unit"] = submission.unit
        return ctx
        
class SubmissionsDownloadView(TeacherRequiredMixin, View):
    """
    Download-ZIP für eine Unit:
    - teacher-only
    - packt alle PDF-Dateien aus SubmissionFile in ein ZIP
    """

    def get(self, request, pk):
        unit = get_object_or_404(Unit.objects.select_related("module"), pk=pk)

        # Alle Dateien der Unit holen (über Submission -> SubmissionFile)
        files_qs = (
            SubmissionFile.objects
            .filter(submission__unit=unit)
            .select_related("submission", "submission__student")
            .order_by("submission__student__username", "id")
        )

        # Nur PDFs
        pdf_files = []
        for sf in files_qs:
            name = (sf.file.name or "").lower()
            if name.endswith(".pdf"):
                pdf_files.append(sf)

        if not pdf_files:
            raise Http404("Keine PDF-Abgaben für diese Einheit vorhanden.")

        buf = io.BytesIO()

        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for sf in pdf_files:
                student = getattr(sf.submission, "student", None)
                username = getattr(student, "username", "unknown")

                # Dateiname im ZIP: <unit>__<username>__<original>.pdf
                original = (sf.file.name.split("/")[-1] or "file.pdf")
                arcname = f"unit_{unit.pk}__{username}__{original}"

                # Dateiinhalt lesen (funktioniert auch mit Remote Storage)
                with sf.file.open("rb") as f:
                    zf.writestr(arcname, f.read())

        buf.seek(0)

        ts = timezone.now().strftime("%Y%m%d_%H%M%S")
        module_part = f"module_{unit.module.order}_" if unit.module_id and unit.module.order is not None else ""
        filename = f"{module_part}unit_{unit.pk}_submissions_{ts}.zip"

        resp = HttpResponse(buf.getvalue(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp


# =============================
# Einladungs-System
# =============================

class TeacherInviteView(TeacherRequiredMixin, View):
    template_name = "modules/teacher_invite.html"

    def get(self, request):
        User = get_user_model()
        invites = InviteToken.objects.filter(created_by=request.user).order_by("-expires_at")
        return render(request, self.template_name, {
            "invites": invites,
            "role_choices": User.ROLE_CHOICES,
        })

    def post(self, request):
        User = get_user_model()
        role = request.POST.get("role", User.STUDENT)
        if role not in dict(User.ROLE_CHOICES):
            role = User.STUDENT
        InviteToken.objects.create(
            created_by=request.user,
            role=role,
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            email=request.POST.get("email", "").strip(),
        )
        return redirect("modules:teacher_invite")


class TeacherInviteDeleteView(TeacherRequiredMixin, View):
    def post(self, request, pk):
        InviteToken.objects.filter(pk=pk, created_by=request.user).delete()
        return redirect("modules:teacher_invite")


class AcceptInviteView(View):
    template_name = "modules/accept_invite.html"

    def _get_token(self, token_str):
        try:
            token = InviteToken.objects.get(token=token_str)
        except (InviteToken.DoesNotExist, ValueError):
            return None
        return token if token.is_valid else None

    def get(self, request, token):
        invite = self._get_token(token)
        if not invite:
            return render(request, self.template_name, {"invalid": True})
        form = AcceptInviteForm()
        return render(request, self.template_name, {"form": form, "invite": invite})

    def post(self, request, token):
        invite = self._get_token(token)
        if not invite:
            return render(request, self.template_name, {"invalid": True})
        form = AcceptInviteForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            cd = form.cleaned_data
            User.objects.create_user(
                username=invite.email,
                first_name=invite.first_name,
                last_name=invite.last_name,
                email=invite.email,
                password=cd["password1"],
                role=invite.role,
            )
            invite.used = True
            invite.save()
            messages.success(request, "Account erstellt — du kannst dich jetzt anmelden.")
            return redirect("login")
        return render(request, self.template_name, {"form": form, "invite": invite})