"""
Tests for submission-related views and teacher/student dashboards.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from modules.models import Module, Unit, Submission, SubmissionFile, ModuleCompletion

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_teacher(**kwargs):
    defaults = {"username": "teacher@t.com", "password": "pass123", "role": User.TEACHER}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_student(**kwargs):
    defaults = {"username": "student@s.com", "password": "pass123", "role": User.STUDENT}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_module(**kwargs):
    defaults = {"title": "Test Modul", "inclass": "x"}
    defaults.update(kwargs)
    return Module.objects.create(**defaults)


def make_unit(module=None, submissions_enabled=True, **kwargs):
    defaults = {
        "date": timezone.now(),
        "submissions_enabled": submissions_enabled,
        "kind": Unit.HOLIDAY,
    }
    defaults.update(kwargs)
    if module:
        defaults["module"] = module
    return Unit.objects.create(**defaults)


def make_submission(unit, student, status=Submission.SUBMITTED):
    return Submission.objects.create(unit=unit, student=student, status=status)


def make_pdf():
    return SimpleUploadedFile("test.pdf", b"%PDF-1.4 fake", content_type="application/pdf")


# ---------------------------------------------------------------------------
# Home redirect
# ---------------------------------------------------------------------------

class RoleBasedHomeRedirectViewTest(TestCase):
    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("modules:home"))
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_teacher_redirects_to_teacher_dashboard(self):
        self.client.force_login(make_teacher())
        response = self.client.get(reverse("modules:home"))
        self.assertRedirects(response, reverse("modules:teacher_dashboard"), fetch_redirect_response=False)

    def test_student_redirects_to_student_dashboard(self):
        self.client.force_login(make_student())
        response = self.client.get(reverse("modules:home"))
        self.assertRedirects(response, reverse("modules:student_dashboard"), fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# EntryToggleCompleteView
# ---------------------------------------------------------------------------

class EntryToggleCompleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = make_student()
        cls.module = make_module(slug="toggle-modul")

    def _url(self):
        return reverse("modules:entry_toggle_complete", kwargs={"slug": self.module.slug})

    def test_post_creates_completion(self):
        self.client.force_login(self.student)
        self.client.post(self._url())
        self.assertTrue(ModuleCompletion.objects.filter(user=self.student, module=self.module).exists())

    def test_post_removes_existing_completion(self):
        ModuleCompletion.objects.create(user=self.student, module=self.module)
        self.client.force_login(self.student)
        self.client.post(self._url())
        self.assertFalse(ModuleCompletion.objects.filter(user=self.student, module=self.module).exists())

    def test_post_redirects_to_next_if_provided(self):
        self.client.force_login(self.student)
        response = self.client.post(self._url(), {"next": "/modules/"})
        self.assertRedirects(response, "/modules/", fetch_redirect_response=False)

    def test_post_redirects_to_list_as_fallback(self):
        self.client.force_login(self.student)
        response = self.client.post(self._url())
        self.assertRedirects(response, reverse("modules:entry_list"), fetch_redirect_response=False)

    def test_requires_login(self):
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ModuleCompletion.objects.filter(module=self.module).exists())


# ---------------------------------------------------------------------------
# TeacherDashboardView context
# ---------------------------------------------------------------------------

class TeacherDashboardContextTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def setUp(self):
        self.client.force_login(self.teacher)

    def test_student_count_correct(self):
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertEqual(response.context["student_count"], 1)

    def test_module_count_correct(self):
        make_module(title="M1")
        make_module(title="M2")
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertEqual(response.context["module_count"], Module.objects.count())

    def test_pending_submissions_count(self):
        unit = make_unit()
        make_submission(unit, self.student, status=Submission.SUBMITTED)
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertEqual(response.context["pending_submissions_count"], 1)

    def test_corrected_submissions_not_counted_as_pending(self):
        unit = make_unit()
        make_submission(unit, self.student, status=Submission.CORRECTED)
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertEqual(response.context["pending_submissions_count"], 0)

    def test_active_unit_context_when_none_enabled(self):
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertIsNone(response.context["active_unit"])


# ---------------------------------------------------------------------------
# StudentDashboardView context
# ---------------------------------------------------------------------------

class StudentDashboardContextTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = make_student()

    def setUp(self):
        self.client.force_login(self.student)

    def test_dashboard_loads(self):
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_completed_count_zero_initially(self):
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertEqual(response.context["completed_count"], 0)

    def test_completed_count_after_toggle(self):
        m = make_module()
        ModuleCompletion.objects.create(user=self.student, module=m)
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertEqual(response.context["completed_count"], 1)

    def test_next_module_is_first_incomplete(self):
        m1 = make_module(title="Eins", order=1)
        m2 = make_module(title="Zwei", order=2)
        ModuleCompletion.objects.create(user=self.student, module=m1)
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertEqual(response.context["next_module"].pk, m2.pk)

    def test_next_module_none_when_all_complete(self):
        m = make_module()
        ModuleCompletion.objects.create(user=self.student, module=m)
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertIsNone(response.context["next_module"])


# ---------------------------------------------------------------------------
# TeacherSubmissionsDashboardView
# ---------------------------------------------------------------------------

class TeacherSubmissionsDashboardTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def setUp(self):
        self.client.force_login(self.teacher)

    def test_page_loads(self):
        response = self.client.get(reverse("modules:teacher_submissions_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_student_count_in_context(self):
        response = self.client.get(reverse("modules:teacher_submissions_dashboard"))
        self.assertEqual(response.context["student_count"], 1)

    def test_units_in_context(self):
        make_unit()
        response = self.client.get(reverse("modules:teacher_submissions_dashboard"))
        self.assertEqual(response.context["total_units"], 1)

    def test_enabled_units_count(self):
        make_unit(submissions_enabled=True)
        make_unit(submissions_enabled=False)
        response = self.client.get(reverse("modules:teacher_submissions_dashboard"))
        self.assertEqual(response.context["enabled_units"], 1)


# ---------------------------------------------------------------------------
# upload_submission_file
# ---------------------------------------------------------------------------

class UploadSubmissionFileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()
        cls.module = make_module()

    def _url(self, unit):
        return reverse("modules:upload_submission_file", kwargs={"unit_id": unit.pk})

    def test_teacher_cannot_upload(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        self.client.force_login(self.teacher)
        response = self.client.post(self._url(unit), {"files": [make_pdf()]})
        self.assertEqual(response.status_code, 403)

    def test_student_upload_creates_submission_and_file(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        self.client.force_login(self.student)
        self.client.post(self._url(unit), {"files": [make_pdf()]})
        self.assertTrue(Submission.objects.filter(unit=unit, student=self.student).exists())
        submission = Submission.objects.get(unit=unit, student=self.student)
        self.assertEqual(submission.files.count(), 1)

    def test_upload_requires_submissions_enabled(self):
        unit = make_unit(module=self.module, submissions_enabled=False)
        self.client.force_login(self.student)
        response = self.client.post(self._url(unit), {"files": [make_pdf()]})
        self.assertEqual(response.status_code, 403)

    def test_upload_blocked_when_already_corrected(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        submission = make_submission(unit, self.student, status=Submission.CORRECTED)
        self.client.force_login(self.student)
        response = self.client.post(self._url(unit), {"files": [make_pdf()]})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(submission.files.count(), 0)

    def test_upload_no_files_shows_warning(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        self.client.force_login(self.student)
        # No files in request
        response = self.client.post(self._url(unit), {})
        # Redirects (warning message), no submission created
        self.assertFalse(Submission.objects.filter(unit=unit, student=self.student).exists())

    def test_upload_redirects_to_module_detail(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        self.client.force_login(self.student)
        response = self.client.post(self._url(unit), {"files": [make_pdf()]})
        self.assertRedirects(
            response,
            reverse("modules:entry_detail", kwargs={"slug": self.module.slug}),
            fetch_redirect_response=False,
        )

    def test_requires_login(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        response = self.client.post(self._url(unit), {"files": [make_pdf()]})
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# delete_submission_file
# ---------------------------------------------------------------------------

class DeleteSubmissionFileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()
        cls.other_student = make_student(username="other@s.com")
        cls.module = make_module()

    def _url(self, sf):
        return reverse("modules:delete_submission_file", kwargs={"file_id": sf.pk})

    def _make_file(self, unit, student):
        submission = make_submission(unit, student)
        sf = SubmissionFile.objects.create(submission=submission, file=make_pdf())
        return sf, submission

    def test_student_can_delete_own_file(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        sf, _ = self._make_file(unit, self.student)
        self.client.force_login(self.student)
        self.client.post(self._url(sf))
        self.assertFalse(SubmissionFile.objects.filter(pk=sf.pk).exists())

    def test_student_cannot_delete_other_students_file(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        sf, _ = self._make_file(unit, self.other_student)
        self.client.force_login(self.student)
        response = self.client.post(self._url(sf))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(SubmissionFile.objects.filter(pk=sf.pk).exists())

    def test_teacher_cannot_delete_file(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        sf, _ = self._make_file(unit, self.student)
        self.client.force_login(self.teacher)
        response = self.client.post(self._url(sf))
        self.assertEqual(response.status_code, 403)

    def test_deleting_last_file_removes_submission(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        sf, submission = self._make_file(unit, self.student)
        self.client.force_login(self.student)
        self.client.post(self._url(sf))
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())

    def test_delete_blocked_for_corrected_submission(self):
        unit = make_unit(module=self.module, submissions_enabled=True)
        # Create as SUBMITTED first, add file, then mark corrected
        submission = make_submission(unit, self.student, status=Submission.SUBMITTED)
        sf = SubmissionFile.objects.create(submission=submission, file=make_pdf())
        Submission.objects.filter(pk=submission.pk).update(status=Submission.CORRECTED)
        self.client.force_login(self.student)
        response = self.client.post(self._url(sf))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(SubmissionFile.objects.filter(pk=sf.pk).exists())


# ---------------------------------------------------------------------------
# teacher_mark_submission_corrected
# ---------------------------------------------------------------------------

class TeacherMarkSubmissionCorrectedTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def _url(self, submission):
        return reverse("modules:teacher_mark_submission_corrected", kwargs={"submission_id": submission.pk})

    def test_teacher_can_mark_corrected(self):
        unit = make_unit()
        sub = make_submission(unit, self.student, status=Submission.SUBMITTED)
        self.client.force_login(self.teacher)
        self.client.post(self._url(sub))
        sub.refresh_from_db()
        self.assertEqual(sub.status, Submission.CORRECTED)

    def test_student_cannot_mark_corrected(self):
        unit = make_unit()
        sub = make_submission(unit, self.student, status=Submission.SUBMITTED)
        self.client.force_login(self.student)
        response = self.client.post(self._url(sub))
        self.assertEqual(response.status_code, 403)
        sub.refresh_from_db()
        self.assertEqual(sub.status, Submission.SUBMITTED)

    def test_already_corrected_stays_corrected(self):
        unit = make_unit()
        sub = make_submission(unit, self.student, status=Submission.CORRECTED)
        self.client.force_login(self.teacher)
        self.client.post(self._url(sub))
        sub.refresh_from_db()
        self.assertEqual(sub.status, Submission.CORRECTED)

    def test_redirects_to_dashboard_by_default(self):
        unit = make_unit()
        sub = make_submission(unit, self.student, status=Submission.SUBMITTED)
        self.client.force_login(self.teacher)
        response = self.client.post(self._url(sub))
        self.assertRedirects(
            response,
            reverse("modules:teacher_submissions_dashboard"),
            fetch_redirect_response=False,
        )

    def test_redirects_to_next_if_provided(self):
        unit = make_unit()
        sub = make_submission(unit, self.student, status=Submission.SUBMITTED)
        self.client.force_login(self.teacher)
        response = self.client.post(self._url(sub), {"next": "/teacher/"})
        self.assertRedirects(response, "/teacher/", fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# teacher_mark_unit_corrected
# ---------------------------------------------------------------------------

class TeacherMarkUnitCorrectedTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()

    def _url(self, unit):
        return reverse("modules:teacher_mark_unit_corrected", kwargs={"unit_id": unit.pk})

    def test_marks_all_submitted_in_unit_corrected(self):
        unit = make_unit()
        s1 = make_student(username="s1@s.com")
        s2 = make_student(username="s2@s.com")
        sub1 = make_submission(unit, s1, status=Submission.SUBMITTED)
        sub2 = make_submission(unit, s2, status=Submission.SUBMITTED)
        self.client.force_login(self.teacher)
        self.client.post(self._url(unit))
        sub1.refresh_from_db()
        sub2.refresh_from_db()
        self.assertEqual(sub1.status, Submission.CORRECTED)
        self.assertEqual(sub2.status, Submission.CORRECTED)

    def test_student_cannot_mark_unit_corrected(self):
        unit = make_unit()
        student = make_student(username="sx@s.com")
        sub = make_submission(unit, student, status=Submission.SUBMITTED)
        self.client.force_login(student)
        response = self.client.post(self._url(unit))
        self.assertEqual(response.status_code, 403)
        sub.refresh_from_db()
        self.assertEqual(sub.status, Submission.SUBMITTED)


# ---------------------------------------------------------------------------
# TeacherToggleUnitSubmissionsView
# ---------------------------------------------------------------------------

class TeacherToggleUnitSubmissionsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher()
        cls.student = make_student()

    def _url(self, unit):
        return reverse("modules:teacher_toggle_unit_submissions", kwargs={"pk": unit.pk})

    def test_toggle_enables_submissions(self):
        unit = make_unit(submissions_enabled=False)
        self.client.force_login(self.teacher)
        self.client.post(self._url(unit))
        unit.refresh_from_db()
        self.assertTrue(unit.submissions_enabled)

    def test_toggle_disables_submissions(self):
        unit = make_unit(submissions_enabled=True)
        self.client.force_login(self.teacher)
        self.client.post(self._url(unit))
        unit.refresh_from_db()
        self.assertFalse(unit.submissions_enabled)

    def test_student_cannot_toggle(self):
        unit = make_unit(submissions_enabled=False)
        self.client.force_login(self.student)
        response = self.client.post(self._url(unit))
        self.assertEqual(response.status_code, 403)
        unit.refresh_from_db()
        self.assertFalse(unit.submissions_enabled)


# ---------------------------------------------------------------------------
# StudentSubmissionsListView
# ---------------------------------------------------------------------------

class StudentSubmissionsListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = make_student()
        cls.teacher = make_teacher()

    def setUp(self):
        self.client.force_login(self.student)

    def test_page_loads(self):
        response = self.client.get(reverse("modules:student_submissions_list"))
        self.assertEqual(response.status_code, 200)

    def test_teacher_gets_403(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("modules:student_submissions_list"))
        self.assertEqual(response.status_code, 403)

    def test_submitted_unit_shows_in_rows(self):
        unit = make_unit(submissions_enabled=True)
        make_submission(unit, self.student, status=Submission.SUBMITTED)
        response = self.client.get(reverse("modules:student_submissions_list"))
        rows = response.context["rows"]
        statuses = [r["status"] for r in rows]
        self.assertIn("submitted", statuses)

    def test_corrected_unit_shows_in_rows(self):
        unit = make_unit(submissions_enabled=True)
        make_submission(unit, self.student, status=Submission.CORRECTED)
        response = self.client.get(reverse("modules:student_submissions_list"))
        rows = response.context["rows"]
        statuses = [r["status"] for r in rows]
        self.assertIn("corrected", statuses)

    def test_open_unit_without_submission_shows_open(self):
        make_unit(submissions_enabled=True)
        response = self.client.get(reverse("modules:student_submissions_list"))
        rows = response.context["rows"]
        statuses = [r["status"] for r in rows]
        self.assertIn("open", statuses)

    def test_counts_match_rows(self):
        make_unit(submissions_enabled=True)
        response = self.client.get(reverse("modules:student_submissions_list"))
        counts = response.context["counts"]
        rows = response.context["rows"]
        total = counts["open"] + counts["submitted"] + counts["corrected"]
        self.assertEqual(total, len(rows))
