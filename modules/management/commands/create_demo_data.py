"""
Management Command: create_demo_data

Erstellt Demo-Nutzer und Beispieldaten für Portfolio-Präsentationen.
Bestehende Demo-Accounts werden dabei nicht doppelt angelegt.

Verwendung:
    python manage.py create_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

DEMO_TEACHER_EMAIL = "lehrer@demo.de"
DEMO_STUDENT_EMAIL = "schueler@demo.de"
DEMO_PASSWORD = "Demo1234!"


class Command(BaseCommand):
    help = "Erstellt Demo-Nutzer und Beispieldaten für Präsentationen."

    def handle(self, *args, **options):
        self._create_users()
        self._create_aufgabentypen()
        self._create_modules()
        self._create_glossary()
        self._print_summary()

    # ------------------------------------------------------------------

    def _create_users(self):
        from accounts.models import InviteToken

        teacher, created = User.objects.get_or_create(
            username=DEMO_TEACHER_EMAIL,
            defaults={
                "email": DEMO_TEACHER_EMAIL,
                "first_name": "Demo",
                "last_name": "Lehrkraft",
                "role": User.TEACHER,
            },
        )
        if created:
            teacher.set_password(DEMO_PASSWORD)
            teacher.save()
            self.stdout.write(self.style.SUCCESS(f"  ✔ Lehrer-Account erstellt: {DEMO_TEACHER_EMAIL}"))
        else:
            self.stdout.write(f"  – Lehrer-Account existiert bereits: {DEMO_TEACHER_EMAIL}")

        student, created = User.objects.get_or_create(
            username=DEMO_STUDENT_EMAIL,
            defaults={
                "email": DEMO_STUDENT_EMAIL,
                "first_name": "Demo",
                "last_name": "Schüler",
                "role": User.STUDENT,
            },
        )
        if created:
            student.set_password(DEMO_PASSWORD)
            student.save()
            self.stdout.write(self.style.SUCCESS(f"  ✔ Schüler-Account erstellt: {DEMO_STUDENT_EMAIL}"))
        else:
            self.stdout.write(f"  – Schüler-Account existiert bereits: {DEMO_STUDENT_EMAIL}")

    def _create_aufgabentypen(self):
        from modules.models import Aufgabentyp

        typen = ["Gehörbildung", "Rhythmus", "Harmonielehre", "Blattlesen"]
        created_count = 0
        for name in typen:
            _, created = Aufgabentyp.objects.get_or_create(name=name)
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f"  ✔ {created_count} Aufgabentypen erstellt"))

    def _create_modules(self):
        from modules.models import Module, Aufgabentyp

        module_data = [
            {
                "title": "Einführung: Das Notensystem",
                "order": 1,
                "inclass": (
                    "Wir lernen die Grundlagen des Notensystems kennen: "
                    "Notenlinien, Schlüssel und die Lage der Stammtöne."
                ),
                "homework": "Lerne die Stammtöne c–h auswendig und schreibe sie auf.",
                "aufgabentypen": ["Gehörbildung"],
            },
            {
                "title": "Rhythmus: Ganze und halbe Noten",
                "order": 2,
                "inclass": (
                    "Ganzen Noten (4 Schläge) und halben Noten (2 Schläge). "
                    "Wir üben einfache Rhythmusmuster durch Klatschen."
                ),
                "homework": "Notiere drei eigene Rhythmusmuster mit ganzen und halben Noten.",
                "aufgabentypen": ["Rhythmus"],
            },
            {
                "title": "Intervalle: Prim bis Quinte",
                "order": 3,
                "inclass": (
                    "Intervalle beschreiben den Abstand zwischen zwei Tönen. "
                    "Wir erarbeiten Prim, Sekunde, Terz, Quarte und Quinte."
                ),
                "homework": "Bestimme alle Intervalle in der Hausaufgaben-Übung.",
                "aufgabentypen": ["Gehörbildung", "Harmonielehre"],
            },
            {
                "title": "Dur-Tonleitern",
                "order": 4,
                "inclass": (
                    "Die Dur-Tonleiter folgt dem Schema Ganz–Ganz–Halb–Ganz–Ganz–Ganz–Halb. "
                    "Wir bauen C-Dur und G-Dur auf."
                ),
                "homework": "Schreibe D-Dur und F-Dur auf und markiere die Halbtonschritte.",
                "aufgabentypen": ["Harmonielehre"],
            },
            {
                "title": "Der Dreiklang",
                "order": 5,
                "inclass": (
                    "Ein Dreiklang besteht aus Grundton, Terz und Quinte. "
                    "Wir unterscheiden Dur- und Moll-Dreiklänge nach ihrer Terz."
                ),
                "homework": "Baue die Dreiklänge auf C, D, E, F, G, A und H auf.",
                "aufgabentypen": ["Harmonielehre", "Gehörbildung"],
            },
        ]

        created_count = 0
        for data in module_data:
            typen_names = data.pop("aufgabentypen")
            module, created = Module.objects.get_or_create(
                title=data["title"],
                defaults={
                    "order": data["order"],
                    "inclass": data["inclass"],
                    "homework": data["homework"],
                },
            )
            if created:
                typen_qs = Aufgabentyp.objects.filter(name__in=typen_names)
                module.tasktype.set(typen_qs)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✔ {created_count} Demo-Module erstellt"))

    def _create_glossary(self):
        from modules.models import GlossaryEntry

        entries = [
            {
                "title": "Intervall",
                "short_definition": "Abstand zwischen zwei Tönen",
                "definition": (
                    "Ein Intervall beschreibt den Tonhöhenabstand zwischen zwei Tönen. "
                    "Er wird in Halbtonschritten oder nach der Stufenbezeichnung angegeben "
                    "(z. B. Terz = 3 Stufen). Intervalle können rein, groß, klein, "
                    "übermäßig oder vermindert sein."
                ),
                "exam_relevant": True,
            },
            {
                "title": "Dreiklang",
                "short_definition": "Übereinanderschichtung dreier Töne im Terzabstand",
                "definition": (
                    "Ein Dreiklang entsteht, wenn drei Töne im Terzabstand übereinandergeschichtet werden. "
                    "Er besteht aus Grundton, Terz und Quinte. Die Qualität (Dur/Moll) "
                    "hängt von der Terz ab: große Terz = Dur, kleine Terz = Moll."
                ),
                "exam_relevant": True,
            },
            {
                "title": "Tonleiter",
                "short_definition": "Geordnete Folge von Tönen innerhalb einer Oktave",
                "definition": (
                    "Eine Tonleiter ist eine geordnete Abfolge von Tönen innerhalb einer Oktave. "
                    "Die Dur-Tonleiter folgt dem Muster G–G–H–G–G–G–H "
                    "(G = Ganzton, H = Halbton). Sie bildet die Grundlage für Melodie und Harmonie."
                ),
                "exam_relevant": True,
            },
            {
                "title": "Takt",
                "short_definition": "Zeitliche Gliederungseinheit in der Musik",
                "definition": (
                    "Der Takt ist die grundlegende Zeiteinheit in der Musik. "
                    "Er wird durch Taktstriche im Notenbild abgegrenzt. "
                    "Die Taktart (z. B. 4/4, 3/4, 6/8) gibt an, wie viele Zählzeiten "
                    "ein Takt enthält und welcher Notenwert eine Zählzeit entspricht."
                ),
                "exam_relevant": False,
            },
            {
                "title": "Halbton",
                "short_definition": "Kleinstmöglicher Tonabstand im westlichen Tonsystem",
                "definition": (
                    "Der Halbton ist das kleinste Intervall in der westlichen Musik. "
                    "Auf dem Klavier entspricht er dem Abstand von einer Taste zur "
                    "unmittelbar benachbarten Taste (z. B. e–f oder h–c)."
                ),
                "exam_relevant": True,
            },
        ]

        created_count = 0
        for data in entries:
            _, created = GlossaryEntry.objects.get_or_create(
                title=data["title"],
                defaults={
                    "short_definition": data["short_definition"],
                    "definition": data["definition"],
                    "exam_relevant": data["exam_relevant"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"  ✔ {created_count} Glossareinträge erstellt"))

    def _print_summary(self):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo-Daten bereit!"))
        self.stdout.write(f"  Lehrer:  {DEMO_TEACHER_EMAIL}")
        self.stdout.write(f"  Schüler: {DEMO_STUDENT_EMAIL}")
        self.stdout.write(f"  Passwort (beide): {DEMO_PASSWORD}")
