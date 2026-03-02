from django.contrib.auth.forms import AuthenticationForm

class RoleLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "placeholder": "Benutzername",
            "class": "auth-input",
            "autocomplete": "username",
            "autofocus": "autofocus",
        })

        self.fields["password"].widget.attrs.update({
            "placeholder": "Passwort",
            "class": "auth-input",
            "autocomplete": "current-password",
        })