from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from modules.models import Module


class ModuleTemplateLogicTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_login(self.user)

    def test_detail_shows_homework_fallback_when_empty(self):
        module = Module.objects.create(
            title="Ohne Homework",
            slug="ohne-homework",
            inclass="Inhalt",
            homework=None,
        )
        url = reverse("modules:entry_detail", kwargs={"slug": module.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "keine Hausaufgabe")

    def test_detail_shows_terms_fallback_when_no_terms(self):
        module = Module.objects.create(
            title="Ohne Begriffe",
            slug="ohne-begriffe",
            inclass="Inhalt",
        )
        url = reverse("modules:entry_detail", kwargs={"slug": module.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "keine Aufgabentypen")

    def test_detail_shows_pdf_fallback_when_no_pdfs(self):
        module = Module.objects.create(
            title="Ohne PDFs",
            slug="ohne-pdfs",
            inclass="Inhalt",
        )
        url = reverse("modules:entry_detail", kwargs={"slug": module.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "keine Dateien vorhanden")

    def test_detail_hides_pdf_fallback_when_pdf_exists(self):
        pdf = SimpleUploadedFile(
            "test.pdf",
            b"%PDF-1.4 fake pdf bytes",
            content_type="application/pdf",
        )

        module = Module.objects.create(
            title="Mit PDF",
            slug="mit-pdf",
            inclass="Inhalt",
            pdf_1=pdf,
        )
        url = reverse("modules:entry_detail", kwargs={"slug": module.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "keine Dateien vorhanden")
        # Optional: prüft, dass der Button-Text gerendert wird
        self.assertContains(response, "Skript")

    def test_detail_shows_audio_fallback_when_no_audio(self):
        module = Module.objects.create(
            title="Ohne Audio",
            slug="ohne-audio",
            inclass="Inhalt",
        )
        url = reverse("modules:entry_detail", kwargs={"slug": module.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "keine Audiodateien vorhanden")

    def test_detail_hides_audio_fallback_when_audio_exists(self):
        audio = SimpleUploadedFile(
            "test.mp3",
            b"fake audio bytes",
            content_type="audio/mpeg",
        )

        module = Module.objects.create(
            title="Mit Audio",
            slug="mit-audio",
            inclass="Inhalt",
            audio_1=audio,
            audio_1_title="Aufgabe 1",
        )
        url = reverse("modules:entry_detail", kwargs={"slug": module.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "keine Audiodateien vorhanden")
        # Optional: Titel wird angezeigt
        self.assertContains(response, "Aufgabe 1")

class ModuleNavigationTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_login(self.user)

    def test_detail_page_contains_next_prev_links(self):
        m1 = Module.objects.create(title="Modul 1", slug="modul-1", inclass="x", order=1)
        m2 = Module.objects.create(title="Modul 2", slug="modul-2", inclass="x", order=2)
        m3 = Module.objects.create(title="Modul 3", slug="modul-3", inclass="x", order=3)

        url = reverse("modules:entry_detail", kwargs={"slug": m2.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Diese beiden asserts prüfen, ob Links auf die Nachbar-Detailseiten im HTML sind:
        self.assertContains(response, reverse("modules:entry_detail", kwargs={"slug": m1.slug}))
        self.assertContains(response, reverse("modules:entry_detail", kwargs={"slug": m3.slug}))
