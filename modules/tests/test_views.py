from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from taggit.models import Tag

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
            slug="test-modul",
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
        
class ModuleViewLogicTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user once for this test class
        User = get_user_model()
        cls.user = User.objects.create_user(username="testuser", password="testpass123")

    def setUp(self):
        self.client.login(username="testuser", password="testpass123")

    # ---------- helpers ----------
    def list_url(self):
        return reverse("modules:entry_list")

    def list_by_tag_url(self, tag_slug: str):
        """
        IMPORTANT: adjust the URL name below to match your urls.py.
        Common choices:
          - "modules:entry_list_by_tag"
          - "modules:entry_list_tag"
          - "modules:entry_list"
        """
        return reverse("modules:entries_by_tag", kwargs={"tag_slug": tag_slug})

    def detail_url(self, slug: str):
        return reverse("modules:entry_detail", kwargs={"slug": slug})

    # ---------- ListView tag filtering ----------
    def test_list_without_tag_returns_all_modules(self):
        Module.objects.create(title="A", inclass="x", order=1)
        Module.objects.create(title="B", inclass="x", order=2)

        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A")
        self.assertContains(response, "B")

    def test_list_filters_by_tag_name_with_umlaut_fallback(self):
        m1 = Module.objects.create(title="Mit Umlaut-Tag", inclass="x", order=1)
        m2 = Module.objects.create(title="Ohne Umlaut-Tag", inclass="x", order=2)

        m1.terms.add("Übung")   # <— nur Umlaut, kein Sonderzeichen-Dash
        tag = Tag.objects.get(name="Übung")

    # Hier testen wir wirklich Fallback #2: name==tag_value
        response = self.client.get(self.list_by_tag_url(tag.name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mit Umlaut-Tag")
        self.assertNotContains(response, "Ohne Umlaut-Tag")
        
    from django.utils.text import slugify

    def test_list_filters_by_tag_slugify_fallback(self):
        m1 = Module.objects.create(title="Mit Tag", inclass="x", order=1)
        m2 = Module.objects.create(title="Ohne Tag", inclass="x", order=2)

        m1.terms.add("My Tag")  # normaler Space, kein Sonder-Dash
        tag = Tag.objects.get(name="My Tag")

    # absichtlich NICHT tag.slug verwenden, sondern slugify(name)
        response = self.client.get(self.list_by_tag_url("my tag"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mit Tag")
        self.assertNotContains(response, "Ohne Tag")

    def test_list_filters_by_tag_name_fallback(self):
        m1 = Module.objects.create(title="Mit Name-Tag", inclass="x", order=1)
        m2 = Module.objects.create(title="Ohne Name-Tag", inclass="x", order=2)

        m1.terms.add("My Tag")
        tag = Tag.objects.get(name="My Tag")

    # trifft Fallback #2: Tag.name == tag_value
        response = self.client.get(self.list_by_tag_url(tag.name))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mit Name-Tag")
        self.assertNotContains(response, "Ohne Name-Tag")


    def test_list_unknown_tag_returns_empty_queryset(self):
        Module.objects.create(title="Modul A", inclass="x", order=1)

        response = self.client.get(self.list_by_tag_url("does-not-exist"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Modul A")

    # ---------- DetailView prev/next context logic ----------
    def test_detail_order_none_sets_prev_next_none(self):
        m = Module.objects.create(title="Ohne Order", inclass="x", order=None)

        response = self.client.get(self.detail_url(m.slug))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["prev_entry"])
        self.assertIsNone(response.context["next_entry"])

    def test_detail_prev_next_tiebreaker_same_order_uses_id(self):
        # same order, increasing ids
        m1 = Module.objects.create(title="M1", inclass="x", order=1)
        m2 = Module.objects.create(title="M2", inclass="x", order=1)
        m3 = Module.objects.create(title="M3", inclass="x", order=1)

        response = self.client.get(self.detail_url(m2.slug))
        self.assertEqual(response.status_code, 200)

        prev_entry = response.context["prev_entry"]
        next_entry = response.context["next_entry"]

        self.assertIsNotNone(prev_entry)
        self.assertIsNotNone(next_entry)
        self.assertEqual(prev_entry.pk, m1.pk)
        self.assertEqual(next_entry.pk, m3.pk)