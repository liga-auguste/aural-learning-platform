from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from taggit.managers import TaggableManager

    
class Entry(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    terms = TaggableManager(verbose_name="Begriffe")
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "entry"
            candidate = base
            i = 2
            while Entry.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural ='Entries'
