from django.contrib import admin
from .models import Module

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "tags_list", "pdf_1", "pdf_2", "pdf_3", "pdf_4")   # Tags sichtbar
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order", "id")
    search_fields = ("title", "inclass", "homework", "tags__name")  # Suche auch nach Tags

    # Hilfsfunktion: Tags kommagetrennt anzeigen
    def tags_list(self, obj):
        return ", ".join(obj.tags.names())
    tags_list.short_description = "Tags"

    