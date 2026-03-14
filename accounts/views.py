from django.contrib.auth.views import LoginView
from django.shortcuts import resolve_url
from .forms import RoleLoginForm


class RoleBasedLoginView(LoginView):
    authentication_form = RoleLoginForm 

    def get_success_url(self):
        user = self.request.user
        next_url = self.get_redirect_url()

        if next_url and not next_url.startswith("/admin"):
            return next_url

        if user.is_teacher:
            return resolve_url("modules:teacher_dashboard")

        if user.is_student:
            return resolve_url("modules:student_dashboard")

        return resolve_url("modules:entry_list")