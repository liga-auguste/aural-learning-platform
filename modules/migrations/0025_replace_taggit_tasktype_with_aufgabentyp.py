import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modules', '0024_delete_unitcompletion'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        # 1) Altes taggit-Feld entfernen
        migrations.RemoveField(
            model_name='module',
            name='tasktype',
        ),
        # 2) Alten Aufgabentyp-Proxy löschen
        migrations.DeleteModel(
            name='Aufgabentyp',
        ),
        # 3) Unit Meta anpassen (war in der generierten Migration dabei)
        migrations.AlterModelOptions(
            name='unit',
            options={
                'ordering': ['date', 'id'],
                'verbose_name': 'Hausaufgabenabgabe',
                'verbose_name_plural': 'Hausaufgabenabgaben',
            },
        ),
        # 4) Neues Aufgabentyp-Model erstellen
        migrations.CreateModel(
            name='Aufgabentyp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('slug', models.SlugField(blank=True, max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Aufgabentyp',
                'verbose_name_plural': 'Aufgabentypen',
                'ordering': ['name'],
            },
        ),
        # 5) Neues M2M-Feld hinzufügen
        migrations.AddField(
            model_name='module',
            name='tasktype',
            field=models.ManyToManyField(
                blank=True,
                related_name='modules',
                to='modules.aufgabentyp',
                verbose_name='Aufgabentypen',
            ),
        ),
    ]
