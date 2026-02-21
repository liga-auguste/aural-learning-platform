from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Erlaubt Zugriff nur für eingeloggte Lehrkräfte (user.is_teacher == True).
    """

    login_url = "login"  # oder dein Login-URL-Name

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and getattr(user, "is_teacher", False)

    def handle_no_permission(self):
        # Wenn nicht eingeloggt -> LoginRequiredMixin handled redirect
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()

        # Eingeloggt, aber keine Lehrkraft -> 403
        raise PermissionDenied("Nur Lehrkräfte dürfen diese Seite aufrufen.")
    
class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "login"

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and getattr(user, "is_student", False)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("Nur Schüler dürfen diese Seite aufrufen.")


class OwnerOrTeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Zugriff, wenn:
    - Lehrkraft, oder
    - Objekt gehört dem eingeloggten User

    Erwartet standardmäßig: self.get_object().user
    Falls dein Feld anders heißt: setze owner_field = "<feldname>"
    """
    login_url = "login"
    owner_field = "user"

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if getattr(user, "is_teacher", False):
            return True

        obj = self.get_object()
        owner = getattr(obj, self.owner_field, None)
        return owner == user

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("Kein Zugriff auf dieses Objekt.")