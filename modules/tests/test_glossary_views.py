"""
Tests for GlossaryListView and glossary_toggle_exam.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from modules.models import GlossaryEntry, Module

User = get_user_model()


def make_teacher(**kwargs):
    defaults = {"username": "teacher@t.com", "password": "pass123", "role": User.TEACHER}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_student(**kwargs):
    defaults = {"username": "student@s.com", "password": "pass123", "role": User.STUDENT}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_term(title, exam_relevant=False, **kwargs):
    return GlossaryEntry.objects.create(title=title, definition="def", exam_relevant=exam_relevant, **kwargs)


# ---------------------------------------------------------------------------
# GlossaryListView
# ---------------------------------------------------------------------------

class GlossaryListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def _url(self, **params):
        url = reverse("modules:glossary_list")
        if params:
            from urllib.parse import urlencode
            url += "?" + urlencode(params)
        return url

    def test_page_loads_for_student(self):
        self.client.force_login(self.student)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)

    def test_requires_login(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_terms_shown_in_context(self):
        make_term("Intervall")
        make_term("Akkord")
        self.client.force_login(self.student)
        response = self.client.get(self._url())
        titles = [t.title for t in response.context["terms"]]
        self.assertIn("Intervall", titles)
        self.assertIn("Akkord", titles)

    def test_filter_exam_only(self):
        make_term("Exam-Begriff", exam_relevant=True)
        make_term("Normal-Begriff", exam_relevant=False)
        self.client.force_login(self.student)
        response = self.client.get(self._url(filter="exam"))
        titles = [t.title for t in response.context["terms"]]
        self.assertIn("Exam-Begriff", titles)
        self.assertNotIn("Normal-Begriff", titles)

    def test_filter_non_exam_only(self):
        make_term("Exam-Begriff", exam_relevant=True)
        make_term("Normal-Begriff", exam_relevant=False)
        self.client.force_login(self.student)
        response = self.client.get(self._url(filter="non_exam"))
        titles = [t.title for t in response.context["terms"]]
        self.assertIn("Normal-Begriff", titles)
        self.assertNotIn("Exam-Begriff", titles)

    def test_sort_az_is_default(self):
        make_term("Zebra")
        make_term("Apfel")
        self.client.force_login(self.student)
        response = self.client.get(self._url())
        titles = [t.title for t in response.context["terms"]]
        self.assertLess(titles.index("Apfel"), titles.index("Zebra"))

    def test_current_filter_in_context(self):
        self.client.force_login(self.student)
        response = self.client.get(self._url(filter="exam"))
        self.assertEqual(response.context["current_filter"], "exam")

    def test_stats_total_in_context(self):
        make_term("T1")
        make_term("T2")
        self.client.force_login(self.student)
        response = self.client.get(self._url())
        self.assertEqual(response.context["stats_total"], GlossaryEntry.objects.count())


# ---------------------------------------------------------------------------
# glossary_toggle_exam
# ---------------------------------------------------------------------------

class GlossaryToggleExamTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def _url(self, term):
        return reverse("modules:glossary_toggle_exam", kwargs={"pk": term.pk})

    def test_teacher_can_toggle_on(self):
        term = make_term("Begriff", exam_relevant=False)
        self.client.force_login(self.teacher)
        self.client.post(self._url(term))
        term.refresh_from_db()
        self.assertTrue(term.exam_relevant)

    def test_teacher_can_toggle_off(self):
        term = make_term("Begriff", exam_relevant=True)
        self.client.force_login(self.teacher)
        self.client.post(self._url(term))
        term.refresh_from_db()
        self.assertFalse(term.exam_relevant)

    def test_student_cannot_toggle(self):
        term = make_term("Begriff", exam_relevant=False)
        self.client.force_login(self.student)
        response = self.client.post(self._url(term))
        self.assertEqual(response.status_code, 403)
        term.refresh_from_db()
        self.assertFalse(term.exam_relevant)

    def test_redirects_to_next_if_provided(self):
        term = make_term("Begriff")
        self.client.force_login(self.teacher)
        response = self.client.post(self._url(term), {"next": "/glossar/?filter=exam"})
        self.assertRedirects(response, "/glossar/?filter=exam", fetch_redirect_response=False)
