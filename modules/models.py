from django.db import models, transaction
from django.db.models import Max
from django.core.validators import FileExtensionValidator
from taggit.managers import TaggableManager
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone
from taggit.models import Tag

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
    tasktype = TaggableManager(verbose_name="Aufgabentypen", blank=True)

    pdf_1 = models.FileField(
        "Skript", upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)
    pdf_2 = models.FileField(
        "Lösung zum Skript", upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)
    pdf_3 = models.FileField(
        "Hausaufgabe", upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)
    pdf_4 = models.FileField(
        "Lösung zur Hausaufgabe", upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)

    order = models.PositiveIntegerField(db_index=True, blank=True, null=True)
    
    audio_1 = models.FileField(
        "Audio Hausaufgabe 1",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
    )
    audio_2 = models.FileField(
        "Audio Hausaufgabe 2",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
    )
    audio_3 = models.FileField(
        "Audio Hausaufgabe 3",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
    )
    audio_4 = models.FileField(
        "Audio Hausaufgabe 4",
        upload_to=module_upload_path,
        validators=[audio_validator],
        blank=True,
        null=True,
    )

    audio_1_title = models.CharField("Titel Audio 1", max_length=120, blank=True)
    audio_2_title = models.CharField("Titel Audio 2", max_length=120, blank=True)
    audio_3_title = models.CharField("Titel Audio 3", max_length=120, blank=True)
    audio_4_title = models.CharField("Titel Audio 4", max_length=120, blank=True)


    def __str__(self):
        return self.title

    class Meta: 
        ordering = ["order", "id"]
        verbose_name = "Module"
        verbose_name_plural = "Module"
        
    def save(self, *args, **kwargs):
        if self.order is None:
            with transaction.atomic():
                max_order = Module.objects.select_for_update().aggregate(m=Max("order"))["m"] or 0
                self.order = max_order + 1

        if not self.slug:
            base = slugify(self.title) or "module"
            candidate = base
            i = 2
            while Module.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate

        super().save(*args, **kwargs)

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
        verbose_name = "Fortschritts-Matrix"
        verbose_name_plural = "Fortschritts-Matrix"
        
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

class Aufgabentyp(Tag):
    class Meta:
        proxy = True
        verbose_name = "Aufgabentyp"
        verbose_name_plural = "Aufgabentypen"
        
class ProgressMatrix:
    class Meta:
        verbose_name = "Fortschritts-Matrix"
        verbose_name_plural = "Fortschritts-Matrix"
        app_label = "modules"