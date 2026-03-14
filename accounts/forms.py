from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

class RoleLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "placeholder": "E-Mail-Adresse",
            "class": "auth-input",
            "autocomplete": "username",
            "autofocus": "autofocus",
        })

        self.fields["password"].widget.attrs.update({
            "placeholder": "Passwort wählen",
            "class": "auth-input",
            "autocomplete": "current-password",
        })


class AcceptInviteForm(forms.Form):
    password1 = forms.CharField(
        label="Passwort",
        widget=forms.PasswordInput(attrs={"class": "auth-input", "placeholder": "Passwort wählen", "autofocus": True}),
    )
    password2 = forms.CharField(
        label="Passwort bestätigen",
        widget=forms.PasswordInput(attrs={"class": "auth-input", "placeholder": "Passwort wiederholen"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Die Passwörter stimmen nicht überein.")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return cleaned