from datetime import timedelta

class RememberMeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.endswith("/accounts/login/") and request.method == "POST":
            # Wenn Login erfolgreich war:
            if request.user.is_authenticated:
                remember = request.POST.get("remember_me") == "on"
                if remember:
                    # z.B. 30 Tage
                    request.session.set_expiry(timedelta(days=30))
                else:
                    # Bis Browser-Schließen
                    request.session.set_expiry(0)
        return response
