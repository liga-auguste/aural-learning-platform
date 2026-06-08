"""
Tests for EntryCreateView, EntryUpdateView, EntryDeleteView,
TaskTypeListView, EntryListView tag filter, contact_view,
and OwnerOrTeacherRequiredMixin (accounts).
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from modules.models import Module, Aufgabentyp, GlossaryEntry

User = get_user_model()


def make_teacher(**kwargs):
    defaults = {"username": "teacher@t.com", "password": "pass123", "role": User.TEACHER}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_student(**kwargs):
    defaults = {"username": "student@s.com", "password": "pass123", "role": User.STUDENT}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_module(**kwargs):
    defaults = {"title": "Modul", "inclass": "Inhalt"}
    defaults.update(kwargs)
    return Module.objects.create(**defaults)


# ---------------------------------------------------------------------------
# EntryCreateView
# ---------------------------------------------------------------------------

class EntryCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def test_teacher_can_access_create_form(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("modules:entry_create"))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_create_form(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("modules:entry_create"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_create_module(self):
        self.client.force_login(self.teacher)
        self.client.post(reverse("modules:entry_create"), {
            "title": "Neues Modul",
            "inclass": "Unterrichtsinhalt",
        })
        self.assertTrue(Module.objects.filter(title="Neues Modul").exists())

    def test_create_redirects_to_list(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("modules:entry_create"), {
            "title": "Weiteres Modul",
            "inclass": "Inhalt",
        })
        self.assertRedirects(response, reverse("modules:entry_list"), fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# EntryUpdateView
# ---------------------------------------------------------------------------

class EntryUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()
        cls.module = make_module(slug="update-modul")

    def _url(self):
        return reverse("modules:entry_update", kwargs={"pk": self.module.pk})

    def test_teacher_can_access_update_form(self):
        self.client.force_login(self.teacher)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_update_form(self):
        self.client.force_login(self.student)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_update_module(self):
        self.client.force_login(self.teacher)
        self.client.post(self._url(), {
            "title": "Geänderter Titel",
            "inclass": "Neuer Inhalt",
        })
        self.module.refresh_from_db()
        self.assertEqual(self.module.title, "Geänderter Titel")

    def test_update_redirects_to_detail(self):
        self.client.force_login(self.teacher)
        response = self.client.post(self._url(), {
            "title": "Update Redirect Test",
            "inclass": "Inhalt",
        })
        self.module.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("modules:entry_detail", kwargs={"slug": self.module.slug}),
            fetch_redirect_response=False,
        )


# ---------------------------------------------------------------------------
# EntryDeleteView
# ---------------------------------------------------------------------------

class EntryDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def test_teacher_can_delete_module(self):
        module = make_module(slug="delete-me")
        self.client.force_login(self.teacher)
        self.client.post(reverse("modules:entry_delete", kwargs={"pk": module.pk}))
        self.assertFalse(Module.objects.filter(pk=module.pk).exists())

    def test_student_cannot_delete_module(self):
        module = make_module(slug="dont-delete-me")
        self.client.force_login(self.student)
        response = self.client.post(reverse("modules:entry_delete", kwargs={"pk": module.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Module.objects.filter(pk=module.pk).exists())

    def test_delete_redirects_to_list(self):
        module = make_module(slug="redirect-after-delete")
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("modules:entry_delete", kwargs={"pk": module.pk}))
        self.assertRedirects(response, reverse("modules:entry_list"), fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# EntryListView — tag filter
# ---------------------------------------------------------------------------

class EntryListTagFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = make_student()
        cls.tag = Aufgabentyp.objects.create(name="Rhythmus")
        cls.m_with_tag = make_module(title="Mit Rhythmus")
        cls.m_with_tag.tasktype.add(cls.tag)
        cls.m_without_tag = make_module(title="Ohne Tag")

    def test_tag_filter_shows_only_tagged(self):
        self.client.force_login(self.student)
        url = reverse("modules:entries_by_tag", kwargs={"tag_slug": self.tag.slug})
        response = self.client.get(url)
        titles = [m.title for m in response.context["entries"]]
        self.assertIn("Mit Rhythmus", titles)
        self.assertNotIn("Ohne Tag", titles)

    def test_unknown_tag_returns_empty(self):
        self.client.force_login(self.student)
        url = reverse("modules:entries_by_tag", kwargs={"tag_slug": "gibts-nicht"})
        response = self.client.get(url)
        self.assertEqual(len(response.context["entries"]), 0)


# ---------------------------------------------------------------------------
# TaskTypeListView
# ---------------------------------------------------------------------------

class TaskTypeListViewTest(TestCase):
    def test_page_loads_without_login(self):
        response = self.client.get(reverse("modules:tasktype_list"))
        self.assertEqual(response.status_code, 200)

    def test_aufgabentypen_in_context(self):
        Aufgabentyp.objects.create(name="Gehörbildung")
        response = self.client.get(reverse("modules:tasktype_list"))
        names = [t.name for t in response.context["tags"]]
        self.assertIn("Gehörbildung", names)


# ---------------------------------------------------------------------------
# contact_view
# ---------------------------------------------------------------------------

class ContactViewTest(TestCase):
    def test_get_renders_form(self):
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_get_includes_contact_email(self):
        response = self.client.get(reverse("contact"))
        self.assertIn("contact_email", response.context)


# ---------------------------------------------------------------------------
# OwnerOrTeacherRequiredMixin (accounts/mixins.py)
# ---------------------------------------------------------------------------

class OwnerOrTeacherRequiredMixinTest(TestCase):
    """
    The mixin is used by StudentSubmissionsDetailView — a student can only
    see their own submission; a teacher can see any.
    """
    from django.utils import timezone

    @classmethod
    def setUpTestData(cls):
        from django.utils import timezone
        from modules.models import Unit, Submission

        cls.teacher = make_teacher()
        cls.student = make_student()
        cls.other_student = make_student(username="other@s.com")

        unit = Unit.objects.create(
            date=timezone.now(),
            kind=Unit.HOLIDAY,
            submissions_enabled=True,
        )
        cls.submission = Submission.objects.create(
            unit=unit,
            student=cls.student,
            status=Submission.SUBMITTED,
        )

    def _url(self, submission=None):
        pk = (submission or self.submission).pk
        return reverse("modules:student_submission_detail", kwargs={"pk": pk})

    def test_owner_can_view_own_submission(self):
        self.client.force_login(self.student)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)

    def test_other_student_gets_404(self):
        self.client.force_login(self.other_student)
        response = self.client.get(self._url())
        # StudentSubmissionsDetailView filters queryset to student's own submissions → 404
        self.assertEqual(response.status_code, 404)

    def test_anonymous_redirected(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)
