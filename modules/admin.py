from django.contrib import admin
from .models import Module

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "tags")     # was angezeigt wird
    list_editable = ("order",)                    # order ist direkt bearbeitbar
    list_display_links = ("title",)               # Titel ist der Link zur Detailseite
    ordering = ("order", "id")                    # Standard-Sortierung
    search_fields = ("title", "inclass", "homework", "tags")
