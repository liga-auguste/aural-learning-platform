from django.contrib import admin
from .models import Module

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "terms_list")   # Begriffe sichtbar
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order", "id")
    search_fields = ("title", "inclass", "homework", "terms__name")  # Suche auch nach Begriffen

    # Hilfsfunktion: Begriffe kommagetrennt anzeigen
    def terms_list(self, obj):
        return ", ".join(obj.terms.names())
    terms_list.short_description = "Begriffe"
