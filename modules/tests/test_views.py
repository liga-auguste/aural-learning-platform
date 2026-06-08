from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from modules.models import Module


class ModuleViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_login(self.user)

    def test_detail_page_loads_for_existing_module(self):
        module = Module.objects.create(
            title="Test Modul",
            inclass="Test Inhalt",
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
        User = get_user_model()
        cls.user = User.objects.create_user(username="testuser", password="testpass123")

    def setUp(self):
        self.client.force_login(self.user)

    def list_url(self):
        return reverse("modules:entry_list")

    def detail_url(self, slug):
        return reverse("modules:entry_detail", kwargs={"slug": slug})

    # ---------- ListView ----------

    def test_list_without_tag_returns_all_modules(self):
        Module.objects.create(title="A", inclass="x", order=1)
        Module.objects.create(title="B", inclass="x", order=2)

        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A")
        self.assertContains(response, "B")

    def test_list_search_filters_by_title(self):
        Module.objects.create(title="Intervalle", inclass="x", order=1)
        Module.objects.create(title="Rhythmus", inclass="x", order=2)

        response = self.client.get(self.list_url(), {"q": "Intervall"})
        self.assertEqual(response.status_code, 200)

        entries = list(response.context["entries"])
        titles = [m.title for m in entries]
        self.assertIn("Intervalle", titles)
        self.assertNotIn("Rhythmus", titles)

    def test_list_search_empty_query_returns_all(self):
        Module.objects.create(title="Intervalle", inclass="x", order=1)
        Module.objects.create(title="Rhythmus", inclass="x", order=2)

        response = self.client.get(self.list_url(), {"q": ""})
        entries = list(response.context["entries"])
        self.assertEqual(len(entries), 2)

    # ---------- DetailView prev/next ----------

    def test_detail_order_none_sets_prev_next_none(self):
        m = Module.objects.create(title="Ohne Order", inclass="x", order=None)

        response = self.client.get(self.detail_url(m.slug))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["prev_entry"])
        self.assertIsNone(response.context["next_entry"])

    def test_detail_prev_next_tiebreaker_same_order_uses_id(self):
        m1 = Module.objects.create(title="M1", inclass="x", order=1)
        m2 = Module.objects.create(title="M2", inclass="x", order=1)
        m3 = Module.objects.create(title="M3", inclass="x", order=1)

        response = self.client.get(self.detail_url(m2.slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["prev_entry"].pk, m1.pk)
        self.assertEqual(response.context["next_entry"].pk, m3.pk)

    def test_detail_first_module_has_no_prev(self):
        m1 = Module.objects.create(title="Erstes", inclass="x", order=1)
        Module.objects.create(title="Zweites", inclass="x", order=2)

        response = self.client.get(self.detail_url(m1.slug))
        self.assertIsNone(response.context["prev_entry"])
        self.assertIsNotNone(response.context["next_entry"])

    def test_detail_last_module_has_no_next(self):
        Module.objects.create(title="Erstes", inclass="x", order=1)
        m2 = Module.objects.create(title="Letztes", inclass="x", order=2)

        response = self.client.get(self.detail_url(m2.slug))
        self.assertIsNotNone(response.context["prev_entry"])
        self.assertIsNone(response.context["next_entry"])

    # ---------- audio_blocks context ----------

    def test_detail_audio_blocks_empty_when_no_audio(self):
        m = Module.objects.create(title="Kein Audio", inclass="x")
        response = self.client.get(self.detail_url(m.slug))
        self.assertEqual(response.context["audio_blocks"], [])

    def test_detail_audio_blocks_contains_uploaded_audio(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        audio = SimpleUploadedFile("test.mp3", b"fake", content_type="audio/mpeg")
        m = Module.objects.create(title="Mit Audio", inclass="x", audio_1=audio, audio_1_title="Track 1")
        response = self.client.get(self.detail_url(m.slug))
        blocks = response.context["audio_blocks"]
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["title"], "Track 1")
