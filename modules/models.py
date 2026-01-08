from django.db import models, transaction
from django.db.models import Max
from django.core.validators import FileExtensionValidator
from taggit.managers import TaggableManager
from django.utils.text import slugify


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
    terms = TaggableManager(verbose_name="Begriffe", blank=True)

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