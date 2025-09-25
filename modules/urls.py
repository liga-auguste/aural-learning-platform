from django.urls import path

from modules import views

urlpatterns = [
    path("", views.home, name="home"),
]
