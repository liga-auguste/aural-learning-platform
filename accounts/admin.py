from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # In der Listenansicht praktisch:
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active", "groups")

    # Damit "role" im Bearbeiten-Formular auftaucht:
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Rolle", {"fields": ("role",)}),
    )

    # Damit "role" auch beim User-Anlegen auftaucht:
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Rolle", {"fields": ("role",)}),
    )

    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)