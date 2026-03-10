# =============================
# Python Standard Library
# =============================
from datetime import timedelta

# =============================
# Django Core
# =============================
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models import Max, Q
from django.utils import timezone
from django.utils.text import slugify

# =============================
# Local Apps
# =============================
from .storages import student_storage, teacher_storage, submissions_storage

def module_upload_path(instance, filename):
    return f"modules/{instance.pk}/{filename}"


pdf_validator = FileExtensionValidator(allowed_extensions=["pdf"])
audio_validator = FileExtensionValidator(
    allowed_extensions=["mp3", "wav", "ogg", "m4a"]
)

class Module(models.Model):
    title = models.CharField("Titel des Moduls", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True)
    inclass = models.TextField("Unterricht")
    homework = models.TextField("Hausaufgabe", blank=True, null=True)
    tasktype = models.ManyToManyField(
        "Aufgabentyp",
        verbose_name="Aufgabentypen",
        blank=True,
        related_name="modules",
    )

    pdf_1 = models.FileField(
        "Skript",
        upload_to=module_upload_path,
        validators=[pdf_validator],
        blank=True,
        null=True,
        storage=student_storage,
    )
    pdf_2 = models.FileField(
        "Lösung zum Skript",
        upload_to=module_upload_path,
        validators=[pdf_validator],
        blank=True,
        null=True,
        storage=teacher_storage,
    )
    pdf_3 = models.FileField(
        "Hausaufgabe",
        upload_to=module_upload_path,
        validators=[pdf_validator],
        blank=True,
        null=True,
        storage=student_storage,
    )
    pdf_4 = models.FileField(
        "Lösung zur Hausaufgabe",
        upload_to=module_upload_path,
        validators=[pdf_validator],
        blank=True,
        null=True,
        storage=teacher_storage,
    )

    order = models.PositiveIntegerField(db_index=True, blank=True, null=True)

    audio_1 = models.FileField(
        "Audio Hausaufgabe 1",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
        storage=student_storage,
    )
    audio_2 = models.FileField(
        "Audio Hausaufgabe 2",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
        storage=student_storage,
    )
    audio_3 = models.FileField(
        "Audio Hausaufgabe 3",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
        storage=student_storage,
    )
    audio_4 = models.FileField(
        "Audio Hausaufgabe 4",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
        storage=student_storage,
    )

    audio_1_title = models.CharField("Titel Audio 1", max_length=120, blank=True)
    audio_2_title = models.CharField("Titel Audio 2", max_length=120, blank=True)
    audio_3_title = models.CharField("Titel Audio 3", max_length=120, blank=True)
    audio_4_title = models.CharField("Titel Audio 4", max_length=120, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Modul"
        verbose_name_plural = "Module"

    def save(self, *args, **kwargs):
        # 1) Order automatisch setzen (falls leer)
        if self.order is None:
            with transaction.atomic():
                max_order = Module.objects.select_for_update().aggregate(m=Max("order"))["m"] or 0
                self.order = max_order + 1

        # 2) Slug automatisch setzen (falls leer)
        if not self.slug:
            base = slugify(self.title) or "module"
            candidate = base
            i = 2
            while Module.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate

        super().save(*args, **kwargs)

        # 3) ✅ Auto-Unit: sobald pdf_3 existiert und noch keine Unit existiert
        # Robust: funktioniert auch, wenn pdf_3 schon früher gesetzt war.
        if self.pdf_3 and not Unit.objects.filter(module_id=self.pk).exists():
            Unit.objects.create(
                module=self,
                kind=getattr(Unit, "REGULAR", "REGULAR"),
                number=self.order,
                date=timezone.now(),          # nötig solange Unit.date NOT NULL ist
                submissions_enabled=False,    # manuelle Freischaltung bleibt standardmäßig aus
            )

class ModuleCompletion(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="module_completions",
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "module"],
                name="unique_completion_per_user_module",
            )
        ]
        indexes = [
            models.Index(fields=["user", "module"]),
            models.Index(fields=["user"]),
        ]
        
        verbose_name = "Fortschrittseintrag"
        verbose_name_plural = "Fortschrittseinträge"

    def __str__(self):
        return f"{self.user} ✓ {self.module}"

class ProgressMatrixProxy(ModuleCompletion):
    class Meta:
        proxy = True
        verbose_name = "Fortschrittsmatrix"
        verbose_name_plural = "Fortschrittsmatrix"
        
class GlossaryEntry(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    short_definition = models.CharField(max_length=300, blank=True)
    definition = models.TextField()
    modules = models.ManyToManyField("modules.Module",related_name="glossary_terms", blank=True)
    exam_relevant = models.BooleanField("Prüfungsrelevanz", default=False)
        
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "begriff"
            candidate = base
            i = 2
            while GlossaryEntry.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate

        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
        
    class Meta:
        verbose_name = "Lernbegriff"
        verbose_name_plural = "Lernbegriffe"

class Aufgabentyp(models.Model):
    name = models.CharField("Name", max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "typ"
            candidate = base
            i = 2
            while Aufgabentyp.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Aufgabentyp"
        verbose_name_plural = "Aufgabentypen"
        ordering = ["name"]
        
class ProgressMatrix:
    class Meta:
        verbose_name = "Fortschritts-Matrix"
        verbose_name_plural = "Fortschritts-Matrix"
        app_label = "modules"
        
class Unit(models.Model):
    REGULAR = "REGULAR"
    HOLIDAY = "HOLIDAY"
    EXAM = "EXAM"
    OTHER = "OTHER"

    KIND_CHOICES = [
        (REGULAR, "Reguläre Einheit"),
        (HOLIDAY, "Ferienaufgabe"),
        (EXAM, "Prüfung/Check"),
        (OTHER, "Sonstiges"),
    ]

    # Global im Kurs: 1–40 (für Ferien/sonstiges darf es leer sein)
    number = models.PositiveSmallIntegerField(
        "Einheit (1–40)",
        blank=True,
        null=True,
        db_index=True,
        help_text="Für reguläre Einheiten 1–40. Für Ferienaufgaben kann es leer bleiben.",
    )

    date = models.DateTimeField(
        "Datum/Zeit der Einheit",
        db_index=True,
        help_text="Startzeit der Einheit (wichtig für 36h-Regel).",
    )

    kind = models.CharField(
        "Typ",
        max_length=20,
        choices=KIND_CHOICES,
        default=REGULAR,
        db_index=True,
    )

    module = models.OneToOneField(
        "modules.Module",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="unit",
        verbose_name="Modul (optional)",
        help_text="Für Ferienaufgaben kann das leer bleiben.",
    )

    submissions_enabled = models.BooleanField(
        "Abgaben freigeschaltet",
        default=False,
        db_index=True,
    )
    
    title = models.CharField(
        "Titel (optional)",
        max_length=200,
        blank=True,
        help_text="Z. B. 'Ferienaufgabe: Intervalle wiederholen' oder 'Klausurvorbereitung'.",
    )

    notes = models.TextField(
        "Notizen/Anweisungen (optional)",
        blank=True,
        help_text="Hier kannst du z. B. Ferien-Aufgabenbeschreibung ablegen, wenn kein Modul verknüpft ist.",
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "id"]
        verbose_name = "Hausaufgabenabgabe"
        verbose_name_plural = "Hausaufgabenabgaben"
        constraints = [
            # Nummer darf (wenn gesetzt) nur einmal vorkommen.
            models.UniqueConstraint(
                fields=["number"],
                condition=models.Q(number__isnull=False),
                name="unique_unit_number_when_set",
            ),
            # Optional: REGULAR-Einheiten müssen eine Nummer haben (Ferien nicht).
            models.CheckConstraint(
                check=(
                    models.Q(kind="HOLIDAY", number__isnull=True)
                    | models.Q(kind="OTHER", number__isnull=True)
                    | models.Q(kind="EXAM", number__isnull=True)
                    | models.Q(kind="REGULAR", number__isnull=False)
                ),
                name="regular_units_require_number",
            ),
        ]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["kind", "date"]),
            models.Index(fields=["number"]),
        ]

    def clean(self):
        super().clean()

        # Wenn number gesetzt ist, begrenze auf 1–40 (dein Kurs-Setting).
        # (Für OTHER/HOLIDAY bleibt number ohnehin meist leer.)
        if self.number is not None and not (1 <= self.number <= 40):
            raise ValidationError({"number": "Die Einheit-Nummer muss zwischen 1 und 40 liegen."})

        # Optional: Bei HOLIDAY/OTHER/EXAM erlauben wir module leer.
        # Bei REGULAR darf module leer sein (z.B. wenn du noch planst),
        # aber du kannst hier auch erzwingen, dass REGULAR ein Modul haben muss.
        # if self.kind == self.REGULAR and self.module is None:
        #     raise ValidationError({"module": "Reguläre Einheiten sollten einem Modul zugeordnet sein."})
        
    def __str__(self):
        date_str = timezone.localtime(self.date).strftime("%Y-%m-%d")

        if self.module:
            order = getattr(self.module, "order", None)
            title = (getattr(self.module, "title", "") or "").strip()

        # Basis: "Modul X" (wenn order existiert) sonst nur Titel
            base = f"Modul {order}" if order is not None else (title or "Modul")

        # Titel nur ergänzen, wenn er nicht redundant ist (z.B. "Modul 1")
            if title and title.lower() != base.lower():
                base = f"{base} – {title}"

            return f"{base} ({date_str})"

        if self.title:
            return f"{self.title} ({date_str})"

        kind_label = dict(self.KIND_CHOICES).get(self.kind, self.kind)
        return f"{kind_label} ({date_str})"

    @property
    def is_regular(self) -> bool:
        return self.kind == self.REGULAR
    
class Submission(models.Model):
    SUBMITTED = "SUBMITTED"
    CORRECTED = "CORRECTED"

    STATUS_CHOICES = [
        (SUBMITTED, "Eingereicht"),
        (CORRECTED, "Korrigiert"),
    ]

    unit = models.ForeignKey(
        "modules.Unit",
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Einheit",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Schüler/in",
    )

    status = models.CharField(
        "Status",
        max_length=20,
        choices=STATUS_CHOICES,
        default=SUBMITTED,
        db_index=True,
    )

    submitted_at = models.DateTimeField("Eingereicht am", blank=True, null=True, db_index=True)
    updated_at = models.DateTimeField("Zuletzt geändert", auto_now=True)

    note_from_student = models.TextField("Notiz (optional)", blank=True)

    class Meta:
        verbose_name = "Abgabe"
        verbose_name_plural = "Abgaben"
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "student"],
                name="unique_submission_per_student_unit",
            ),
        ]
        indexes = [
            models.Index(fields=["unit", "status"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["unit", "student"]),
        ]

    def __str__(self):
        u = self.unit.number if self.unit.number is not None else "—"
        return f"Abgabe: Einheit {u} – {self.student}"

    def is_editable_by_student(self, now=None) -> bool:
        """
        TEMPORÄR: Lock komplett deaktiviert.
        True = Schüler darf Files hinzufügen/löschen/ersetzen.

        Regeln:
        1) Unit muss freigeschaltet sein (unit.submissions_enabled)
        2) Nach "korrigiert" keine Änderungen (optional, aber sinnvoll)
        """
        # 1) ✅ manuelle Freischaltung
        if not getattr(self.unit, "submissions_enabled", False):
            return False

        # 2) ✅ nach "korrigiert" nie editierbar
        if self.status == self.CORRECTED:
            return False

        return True

    def clean(self):
        super().clean()

        # Safety: Sicherstellen, dass wirklich Student-Role.
        if hasattr(self.student, "is_student") and not self.student.is_student:
            raise ValidationError({"student": "Nur Nutzer mit Rolle 'Schüler' können Abgaben haben."})
        
        # ✅ Regel: "Eingereicht" / "Korrigiert" nur, wenn mind. 1 Datei existiert
        # (bei neuem Objekt ohne pk kann man Inlines noch nicht prüfen)
        if self.pk and self.status in {self.SUBMITTED, self.CORRECTED}:
            if not self.files.exists():
                raise ValidationError({
                    "status": "Status 'Eingereicht'/'Korrigiert' ist nur erlaubt, wenn mindestens eine PDF hochgeladen wurde."}
                )


def submission_file_upload_path(instance: "SubmissionFile", filename: str) -> str:
    """
    Speicherpfad: sauber sortierbar nach Einheit/Datum/Schüler.
    Robust auch dann, wenn unit.date noch nicht gesetzt ist.
    """
    unit = instance.submission.unit
    student = instance.submission.student

    unit_num = unit.number if unit.number is not None else "x"

    if unit.date:
        date_str = timezone.localtime(unit.date).strftime("%Y-%m-%d")
    else:
        date_str = "unscheduled"

    return f"submissions/unit_{unit_num}/{date_str}/student_{student.id}/{filename}"

class SubmissionFile(models.Model):
    submission = models.ForeignKey(
        "modules.Submission",
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name="Abgabe",
    )

    file = models.FileField(
        "PDF",
        upload_to=submission_file_upload_path,
        validators=[pdf_validator],
        storage=submissions_storage,
    )

    uploaded_at = models.DateTimeField(default=timezone.now, editable=False)

    display_name = models.CharField("Anzeigename (optional)", max_length=200, blank=True)
    position = models.PositiveSmallIntegerField("Reihenfolge", blank=True, null=True)

    class Meta:
        verbose_name = "Abgabe-Datei"
        verbose_name_plural = "Abgabe-Dateien"
        ordering = ["position", "uploaded_at", "id"]
        indexes = [
            models.Index(fields=["submission", "uploaded_at"]),
        ]

    def __str__(self):
        return f"Datei zu Submission #{self.submission_id}"

    def clean(self):
        super().clean()

        # Sperren: nicht freigeschaltet / 36h-Regel / bereits korrigiert
        if self.submission_id and not self.submission.is_editable_by_student():
            raise ValidationError(
                "Uploads/Änderungen sind gesperrt (nicht freigeschaltet, 36h-Regel oder bereits korrigiert)."
            )

    def save(self, *args, **kwargs):
        creating = self._state.adding

        # sicherstellen, dass clean() + Field-Validatoren laufen
        self.full_clean()
        super().save(*args, **kwargs)

        # beim ersten Upload: Submission als eingereicht markieren
        if creating:
            Submission.objects.filter(
                pk=self.submission_id,
                submitted_at__isnull=True,
            ).update(
                submitted_at=timezone.now(),
                status=Submission.SUBMITTED,
            )