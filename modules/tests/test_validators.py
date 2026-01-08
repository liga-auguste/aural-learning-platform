from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from modules.models import Module


class ModulePdfValidatorTest(TestCase):
    def test_pdf_validator_accepts_pdf(self):
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            b"%PDF-1.4 fake pdf bytes",
            content_type="application/pdf",
        )

        module = Module(
            title="PDF Modul",
            slug="pdf-modul",
            inclass="Inhalt",
            pdf_1=pdf_file,
        )

        # darf keinen ValidationError werfen
        module.full_clean()

    def test_pdf_validator_rejects_non_pdf(self):
        not_pdf = SimpleUploadedFile(
            "test.txt",
            b"Just some text",
            content_type="text/plain",
        )

        module = Module(
            title="Kein PDF",
            slug="kein-pdf",
            inclass="Inhalt",
            pdf_1=not_pdf,
        )

        with self.assertRaises(ValidationError):
            module.full_clean()


class ModuleAudioValidatorTest(TestCase):
    def test_audio_validator_accepts_allowed_extensions(self):
        allowed_files = [
            ("test.mp3", "audio/mpeg"),
            ("test.wav", "audio/wav"),
            ("test.ogg", "audio/ogg"),
            ("test.m4a", "audio/mp4"),
        ]

        for filename, content_type in allowed_files:
            with self.subTest(filename=filename):
                audio_file = SimpleUploadedFile(
                    filename,
                    b"fake audio bytes",
                    content_type=content_type,
                )

                # Slug garantiert gültig (nur Buchstaben + Bindestrich),
                # und je Subtest eindeutig
                ext = filename.rsplit(".", 1)[1]  # mp3/wav/ogg/m4a
                safe_slug = f"audio-{ext}"

                module = Module(
                    title="Audio Modul",
                    slug=safe_slug,
                    inclass="Inhalt",
                    audio_1=audio_file,
                )

                module.full_clean()  # darf keinen ValidationError werfen

    def test_audio_validator_rejects_non_audio(self):
        not_audio = SimpleUploadedFile(
            "test.txt",
            b"Just some text",
            content_type="text/plain",
        )

        module = Module(
            title="Kein Audio",
            slug="kein-audio",
            inclass="Inhalt",
            audio_1=not_audio,
        )

        with self.assertRaises(ValidationError):
            module.full_clean()
