from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from modules.models import Module

class ModuleViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser",password="testpass123")
        self.client.login(username="testuser", password="testpass123")
    
    def test_detail_page_loads_for_existing_module(self):
        module = Module.objects.create(
            title= "Test Modul",
            inclass= "Test Inhalt",
        )
        
        url = reverse("modules:entry_detail", kwargs={"slug": "test-modul"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Modul")

    def test_module_detail_404_for_unknown_slug(self):
        url = reverse("modules:entry_detail", kwargs={"slug": "does-not-exist"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
    
    def test_module_list_shows_modules(self):
        Module.objects.create(title="A Modul", slug="a-modul", inclass="A", order=2)
        Module.objects.create(title="B Modul", slug="b-modul", inclass="B", order=1)

        url = reverse("modules:entry_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A Modul")
        self.assertContains(response, "B Modul")
    
    def test_module_list_is_sorted_by_order(self):
        Module.objects.create(title="A Modul", slug="a-modul", inclass="A", order=2)
        Module.objects.create(title="B Modul", slug="b-modul", inclass="B", order=1)

        url = reverse("modules:entry_list")
        response = self.client.get(url)

        content = response.content.decode("utf-8")
        self.assertLess(content.index("B Modul"), content.index("A Modul"))