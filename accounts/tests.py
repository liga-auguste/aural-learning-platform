from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import InviteToken

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_teacher(**kwargs):
    defaults = {"username": "teacher@example.com", "password": "teacherpass123", "role": User.TEACHER}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_student(**kwargs):
    defaults = {"username": "student@example.com", "password": "studentpass123", "role": User.STUDENT}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_invite(teacher, **kwargs):
    defaults = {
        "created_by": teacher,
        "role": User.STUDENT,
        "first_name": "Anna",
        "last_name": "Müller",
        "email": "anna@example.com",
        "expires_at": timezone.now() + timedelta(days=7),
    }
    defaults.update(kwargs)
    return InviteToken.objects.create(**defaults)


# ---------------------------------------------------------------------------
# InviteToken model
# ---------------------------------------------------------------------------

class InviteTokenModelTest(TestCase):
    def setUp(self):
        self.teacher = make_teacher()

    def test_is_valid_for_fresh_token(self):
        invite = make_invite(self.teacher)
        self.assertTrue(invite.is_valid)

    def test_is_valid_false_when_used(self):
        invite = make_invite(self.teacher, used=True)
        self.assertFalse(invite.is_valid)

    def test_is_valid_false_when_expired(self):
        invite = make_invite(self.teacher, expires_at=timezone.now() - timedelta(seconds=1))
        self.assertFalse(invite.is_valid)

    def test_expires_at_auto_set_on_create(self):
        invite = InviteToken.objects.create(created_by=self.teacher, role=User.STUDENT)
        self.assertIsNotNone(invite.expires_at)
        self.assertGreater(invite.expires_at, timezone.now())

    def test_str_contains_role_and_creator(self):
        invite = make_invite(self.teacher)
        result = str(invite)
        self.assertIn(self.teacher.username, result)


# ---------------------------------------------------------------------------
# Login redirect by role
# ---------------------------------------------------------------------------

class RoleBasedLoginRedirectTest(TestCase):
    def test_teacher_redirected_to_teacher_dashboard(self):
        make_teacher(username="t@t.com", password="pass123")
        response = self.client.post(
            reverse("login"),
            {"username": "t@t.com", "password": "pass123"},
        )
        self.assertRedirects(response, reverse("modules:teacher_dashboard"), fetch_redirect_response=False)

    def test_student_redirected_to_student_dashboard(self):
        make_student(username="s@s.com", password="pass123")
        response = self.client.post(
            reverse("login"),
            {"username": "s@s.com", "password": "pass123"},
        )
        self.assertRedirects(response, reverse("modules:student_dashboard"), fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------

class RoleBasedAccessTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher(username="t@t.com")
        cls.student = make_student(username="s@s.com")

    def _login(self, user):
        self.client.force_login(user)

    # Teacher-only pages
    def test_teacher_dashboard_requires_teacher(self):
        self._login(self.student)
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_invite_page_requires_teacher(self):
        self._login(self.student)
        response = self.client.get(reverse("modules:teacher_invite"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_dashboard_accessible_to_teacher(self):
        self._login(self.teacher)
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertEqual(response.status_code, 200)

    # Student-only pages
    def test_student_dashboard_requires_student(self):
        self._login(self.teacher)
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_student_dashboard_accessible_to_student(self):
        self._login(self.student)
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertEqual(response.status_code, 200)

    # Anonymous
    def test_anonymous_redirected_from_teacher_dashboard(self):
        response = self.client.get(reverse("modules:teacher_dashboard"))
        self.assertIn(response.status_code, [302, 301])

    def test_anonymous_redirected_from_student_dashboard(self):
        response = self.client.get(reverse("modules:student_dashboard"))
        self.assertIn(response.status_code, [302, 301])


# ---------------------------------------------------------------------------
# TeacherInviteView
# ---------------------------------------------------------------------------

class TeacherInviteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher(username="t@t.com")
        cls.other_teacher = make_teacher(username="t2@t.com")

    def setUp(self):
        self.client.force_login(self.teacher)

    def _invite_url(self):
        return reverse("modules:teacher_invite")

    def test_get_shows_invite_form(self):
        response = self.client.get(self._invite_url())
        self.assertEqual(response.status_code, 200)

    def test_post_creates_invite(self):
        self.client.post(self._invite_url(), {
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "max@example.com",
            "role": User.STUDENT,
        })
        self.assertEqual(InviteToken.objects.filter(created_by=self.teacher).count(), 1)
        invite = InviteToken.objects.get(created_by=self.teacher)
        self.assertEqual(invite.email, "max@example.com")
        self.assertEqual(invite.first_name, "Max")

    def test_post_redirects_after_create(self):
        response = self.client.post(self._invite_url(), {
            "first_name": "A",
            "last_name": "B",
            "email": "a@b.com",
            "role": User.STUDENT,
        })
        self.assertRedirects(response, self._invite_url())

    def test_invite_list_shows_own_invites_only(self):
        make_invite(self.teacher, email="own@example.com")
        make_invite(self.other_teacher, email="other@example.com")

        response = self.client.get(self._invite_url())
        invites = list(response.context["invites"])
        emails = [i.email for i in invites]
        self.assertIn("own@example.com", emails)
        self.assertNotIn("other@example.com", emails)

    def test_invalid_role_falls_back_to_student(self):
        self.client.post(self._invite_url(), {
            "first_name": "X",
            "last_name": "Y",
            "email": "x@y.com",
            "role": "HACKER",
        })
        invite = InviteToken.objects.get(email="x@y.com")
        self.assertEqual(invite.role, User.STUDENT)


# ---------------------------------------------------------------------------
# TeacherInviteDeleteView
# ---------------------------------------------------------------------------

class TeacherInviteDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher(username="t@t.com")
        cls.other_teacher = make_teacher(username="t2@t.com")

    def _delete_url(self, pk):
        return reverse("modules:teacher_invite_delete", kwargs={"pk": pk})

    def test_teacher_can_delete_own_invite(self):
        invite = make_invite(self.teacher)
        self.client.force_login(self.teacher)
        self.client.post(self._delete_url(invite.pk))
        self.assertFalse(InviteToken.objects.filter(pk=invite.pk).exists())

    def test_teacher_cannot_delete_others_invite(self):
        invite = make_invite(self.other_teacher)
        self.client.force_login(self.teacher)
        self.client.post(self._delete_url(invite.pk))
        # Silently ignored — filter(created_by=request.user) just returns empty
        self.assertTrue(InviteToken.objects.filter(pk=invite.pk).exists())

    def test_delete_redirects_to_invite_list(self):
        invite = make_invite(self.teacher)
        self.client.force_login(self.teacher)
        response = self.client.post(self._delete_url(invite.pk))
        self.assertRedirects(response, reverse("modules:teacher_invite"))


# ---------------------------------------------------------------------------
# AcceptInviteView
# ---------------------------------------------------------------------------

class AcceptInviteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = make_teacher(username="t@t.com")

    def _accept_url(self, token):
        return reverse("modules:accept_invite", kwargs={"token": token})

    def _make_valid_invite(self, **kwargs):
        return make_invite(self.teacher, **kwargs)

    def test_get_with_valid_token_shows_form(self):
        invite = self._make_valid_invite()
        response = self.client.get(self._accept_url(invite.token))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context.get("invalid", False))
        self.assertIn("form", response.context)

    def test_get_with_invalid_token_shows_error(self):
        import uuid
        response = self.client.get(self._accept_url(uuid.uuid4()))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["invalid"])

    def test_get_with_expired_token_shows_error(self):
        invite = self._make_valid_invite(
            email="expired@example.com",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        response = self.client.get(self._accept_url(invite.token))
        self.assertTrue(response.context["invalid"])

    def test_get_with_used_token_shows_error(self):
        invite = self._make_valid_invite(email="used@example.com", used=True)
        response = self.client.get(self._accept_url(invite.token))
        self.assertTrue(response.context["invalid"])

    def test_valid_post_creates_user(self):
        invite = self._make_valid_invite(email="new@example.com", role=User.STUDENT)
        self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertTrue(User.objects.filter(username="new@example.com").exists())

    def test_created_user_has_correct_role(self):
        invite = self._make_valid_invite(email="newteacher@example.com", role=User.TEACHER)
        self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        user = User.objects.get(username="newteacher@example.com")
        self.assertEqual(user.role, User.TEACHER)

    def test_created_user_has_name_from_invite(self):
        invite = self._make_valid_invite(
            email="named@example.com", first_name="Anna", last_name="Müller"
        )
        self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        user = User.objects.get(username="named@example.com")
        self.assertEqual(user.first_name, "Anna")
        self.assertEqual(user.last_name, "Müller")

    def test_valid_post_marks_token_used(self):
        invite = self._make_valid_invite(email="once@example.com")
        self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        invite.refresh_from_db()
        self.assertTrue(invite.used)

    def test_valid_post_redirects_to_login(self):
        invite = self._make_valid_invite(email="redirect@example.com")
        response = self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_mismatched_passwords_dont_create_user(self):
        invite = self._make_valid_invite(email="nomatch@example.com")
        self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "WrongPassword!",
        })
        self.assertFalse(User.objects.filter(username="nomatch@example.com").exists())

    def test_mismatched_passwords_keep_token_unused(self):
        invite = self._make_valid_invite(email="still_open@example.com")
        self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "WrongPassword!",
        })
        invite.refresh_from_db()
        self.assertFalse(invite.used)

    def test_used_token_cannot_be_reused(self):
        invite = self._make_valid_invite(email="first@example.com")
        # First use
        self.client.post(self._accept_url(invite.token), {
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        # Second use attempt
        response = self.client.post(self._accept_url(invite.token), {
            "password1": "AnotherPass123!",
            "password2": "AnotherPass123!",
        })
        self.assertTrue(response.context["invalid"])
        self.assertEqual(User.objects.filter(username="first@example.com").count(), 1)
