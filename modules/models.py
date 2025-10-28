from django.db import models, transaction
from django.db.models import Max
from django.core.validators import FileExtensionValidator
from taggit.managers import TaggableManager



def module_upload_path(instance, filename):
    return f"modules/{instance.pk}/{filename}"


pdf_validator = FileExtensionValidator(allowed_extensions=["pdf"])


class Module(models.Model):
    title = models.CharField("Titel des Moduls", max_length=200)
    inclass = models.TextField("Unterricht")                      # früher: content
    homework = models.TextField("Hausaufgabe", blank=True, null=True)
    tags = TaggableManager(verbose_name="Begriffe", blank=True)

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
        super().save(*args, **kwargs)