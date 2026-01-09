# modules/context_processors.py
from .models import Module

def nav_modules(request):
    return {
        "nav_modules": Module.objects.order_by("order")
    }
