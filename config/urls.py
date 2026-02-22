from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from modules.views import contact_view
from accounts.views import RoleBasedLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", RoleBasedLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),

    # modules app mounted at root:
    path("", include(("modules.urls", "modules"), namespace="modules")),

    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("impressum/", TemplateView.as_view(template_name="impressum.html"), name="impressum"),
    path("datenschutz/", TemplateView.as_view(template_name="datenschutz.html"), name="datenschutz"),
    path("kontakt/", contact_view, name="contact"),
    path("kontakt/danke/", TemplateView.as_view(template_name="contact_thanks.html"), name="contact_thanks"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)