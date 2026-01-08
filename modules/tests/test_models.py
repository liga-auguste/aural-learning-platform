from django.test import TestCase

from modules.models import Module

class ModuleModelTest(TestCase):
    def test_str_returns_title(self):
        module = Module.objects.create(
            title="Mein Testmodul",
            slug="mein-testmodul",
            inclass="Inhalt"
        )

        self.assertEqual(str(module), "Mein Testmodul")
        
    def test_slug_is_generated_from_title(self):
        m = Module.objects.create(
            title="Mein Modul",
            inclass="x")
        self.assertEqual(m.slug, "mein-modul")

    def test_slug_is_made_unique(self):
        m1 = Module.objects.create(title="Mein Modul", inclass="x")
        m2 = Module.objects.create(title="Mein Modul", inclass="x")
        
        self.assertEqual(m1.slug, "mein-modul")
        self.assertEqual(m2.slug, "mein-modul-2")
