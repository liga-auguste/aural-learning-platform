from django.db import models
from django.core.validators import FileExtensionValidator


def module_upload_path(instance, filename):
    return f"modules/{instance.pk or 'tmp'}/{filename}"


pdf_validator = FileExtensionValidator(allowed_extensions=["pdf"])


class Module(models.Model):
    title = models.CharField(max_length=200)
    inclass = models.TextField()                      # früher: content
    homework = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True)

    pdf_1 = models.FileField(upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)
    pdf_2 = models.FileField(upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)
    pdf_3 = models.FileField(upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)
    pdf_4 = models.FileField(upload_to=module_upload_path, validators=[pdf_validator],
                             blank=True, null=True)

    order = models.PositiveIntegerField(default=0, db_index=True)

    def __str__(self):
        return self.title

    class Meta: 
        ordering = ["order", "id"]