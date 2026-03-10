"""
Data migration: kopiert bestehende taggit-Tags (aus taggit_tag / taggit_taggeditem)
in das neue Aufgabentyp-Model und stellt die M2M-Verknüpfungen zu Modulen wieder her.
"""
from django.db import migrations
from django.utils.text import slugify


def migrate_tags_forward(apps, schema_editor):
    Aufgabentyp = apps.get_model("modules", "Aufgabentyp")
    Module = apps.get_model("modules", "Module")

    db = schema_editor.connection

    # taggit speichert Tags generisch über ContentType.
    # Wir lesen direkt aus taggit_tag und taggit_taggeditem.
    with db.cursor() as cursor:
        # Content Type für modules.Module ermitteln
        cursor.execute(
            "SELECT id FROM django_content_type WHERE app_label = %s AND model = %s",
            ["modules", "module"],
        )
        row = cursor.fetchone()
        if not row:
            return  # Kein ContentType → nichts zu migrieren
        content_type_id = row[0]

        # Alle Tag-Module-Paare aus taggit holen
        cursor.execute(
            """
            SELECT t.name, t.slug, ti.object_id
            FROM taggit_tag t
            JOIN taggit_taggeditem ti ON ti.tag_id = t.id
            WHERE ti.content_type_id = %s
            """,
            [content_type_id],
        )
        rows = cursor.fetchall()

    for tag_name, tag_slug, module_id in rows:
        # Aufgabentyp anlegen (oder vorhandenen holen)
        aufgabentyp, _ = Aufgabentyp.objects.get_or_create(
            name=tag_name,
            defaults={"slug": tag_slug or slugify(tag_name) or "typ"},
        )

        # Modul verknüpfen
        try:
            module = Module.objects.get(pk=module_id)
            module.tasktype.add(aufgabentyp)
        except Module.DoesNotExist:
            pass


def migrate_tags_backward(apps, schema_editor):
    # Rückrichtung: einfach alle Aufgabentypen löschen
    Aufgabentyp = apps.get_model("modules", "Aufgabentyp")
    Aufgabentyp.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("modules", "0025_replace_taggit_tasktype_with_aufgabentyp"),
        ("taggit", "0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx"),
    ]

    operations = [
        migrations.RunPython(migrate_tags_forward, migrate_tags_backward),
    ]
