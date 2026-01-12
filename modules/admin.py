from django.contrib import admin
from .models import Module, GlossaryEntry

admin.site.register(GlossaryEntry)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "title",
        "terms_list",
        "has_homework",
        "pdf_count",
        "audio_count",
        "slug",
    )
    
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

class GlossaryEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "exam_relevant")
    list_filter = ("exam_relevant",)
    search_fields = ("title", "definition")
    prepopulated_fields = {"slug": ("title",)}