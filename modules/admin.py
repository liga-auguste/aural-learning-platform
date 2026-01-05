from django.contrib import admin
from .models import Module

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("order", "title", "terms_list", "pdf_1", "pdf_2", "pdf_3", "pdf_4")
    list_editable = ("order",)
    list_display_links = ("title",)
    ordering = ("order", "id")
    search_fields = ("title", "inclass", "homework", "terms__name")

    def terms_list(self, obj):
        return ", ".join(obj.terms.names())
    terms_list.short_description = "Begriffe"
