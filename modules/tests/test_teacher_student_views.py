"""
Tests for teacher-facing student management views:
- TeacherStudentListView
- TeacherStudentDetailView
- TeacherToggleCompletionView
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from modules.models import Module, ModuleCompletion, Unit, Submission
from django.utils import timezone

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
    defaults = {"title": "Modul", "inclass": "x"}
    defaults.update(kwargs)
    return Module.objects.create(**defaults)


def make_unit(module=None, **kwargs):
    defaults = {"date": timezone.now(), "kind": Unit.HOLIDAY, "submissions_enabled": False}
    defaults.update(kwargs)
    if module:
        defaults["module"] = module
    return Unit.objects.create(**defaults)


# ---------------------------------------------------------------------------
# TeacherStudentListView
# ---------------------------------------------------------------------------

class TeacherStudentListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def setUp(self):
        self.client.force_login(self.teacher)

    def test_page_loads(self):
        response = self.client.get(reverse("modules:teacher_student_list"))
        self.assertEqual(response.status_code, 200)

    def test_student_in_list(self):
        response = self.client.get(reverse("modules:teacher_student_list"))
        usernames = [d["student"].username for d in response.context["students_data"]]
        self.assertIn(self.student.username, usernames)

    def test_teacher_not_in_list(self):
        response = self.client.get(reverse("modules:teacher_student_list"))
        usernames = [d["student"].username for d in response.context["students_data"]]
        self.assertNotIn(self.teacher.username, usernames)

    def test_completed_count_shown(self):
        m = make_module()
        ModuleCompletion.objects.create(user=self.student, module=m)
        response = self.client.get(reverse("modules:teacher_student_list"))
        data = {d["student"].pk: d for d in response.context["students_data"]}
        self.assertEqual(data[self.student.pk]["completed"], 1)

    def test_total_modules_in_context(self):
        make_module(title="M1")
        make_module(title="M2")
        response = self.client.get(reverse("modules:teacher_student_list"))
        self.assertEqual(response.context["total_modules"], Module.objects.count())

    def test_student_gets_403(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("modules:teacher_student_list"))
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# TeacherStudentDetailView
# ---------------------------------------------------------------------------

class TeacherStudentDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def _url(self, student=None):
        pk = (student or self.student).pk
        return reverse("modules:teacher_student_detail", kwargs={"pk": pk})

    def setUp(self):
        self.client.force_login(self.teacher)

    def test_page_loads(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)

    def test_student_in_context(self):
        response = self.client.get(self._url())
        self.assertEqual(response.context["student"].pk, self.student.pk)

    def test_module_rows_in_context(self):
        make_module()
        response = self.client.get(self._url())
        self.assertEqual(len(response.context["module_rows"]), Module.objects.count())

    def test_completed_count_reflects_completions(self):
        m = make_module()
        ModuleCompletion.objects.create(user=self.student, module=m)
        response = self.client.get(self._url())
        self.assertEqual(response.context["completed_count"], 1)

    def test_404_for_nonexistent_student(self):
        url = reverse("modules:teacher_student_detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_404_when_pk_is_teacher(self):
        url = reverse("modules:teacher_student_detail", kwargs={"pk": self.teacher.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_hw_corrected_count(self):
        unit = make_unit()
        Submission.objects.create(unit=unit, student=self.student, status=Submission.CORRECTED)
        response = self.client.get(self._url())
        self.assertEqual(response.context["hw_corrected"], 1)
        self.assertEqual(response.context["hw_submitted"], 0)


# ---------------------------------------------------------------------------
# TeacherToggleCompletionView
# ---------------------------------------------------------------------------

class TeacherToggleCompletionViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()
        cls.module = make_module(slug="toggle-mod")

    def _url(self):
        return reverse(
            "modules:teacher_toggle_completion",
            kwargs={"pk": self.student.pk, "slug": self.module.slug},
        )

    def test_teacher_can_create_completion(self):
        self.client.force_login(self.teacher)
        self.client.post(self._url())
        self.assertTrue(ModuleCompletion.objects.filter(user=self.student, module=self.module).exists())

    def test_teacher_can_remove_completion(self):
        ModuleCompletion.objects.create(user=self.student, module=self.module)
        self.client.force_login(self.teacher)
        self.client.post(self._url())
        self.assertFalse(ModuleCompletion.objects.filter(user=self.student, module=self.module).exists())

    def test_redirects_to_student_detail(self):
        self.client.force_login(self.teacher)
        response = self.client.post(self._url())
        self.assertRedirects(
            response,
            reverse("modules:teacher_student_detail", kwargs={"pk": self.student.pk}),
            fetch_redirect_response=False,
        )

    def test_student_cannot_toggle_others_completion(self):
        self.client.force_login(self.student)
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 403)
