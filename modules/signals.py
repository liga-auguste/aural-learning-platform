from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import F

from .models import Module


@receiver(post_delete, sender=Module)
def renumber_on_delete(sender, instance, **kwargs):
    if instance.order is None:
        return

    Module.objects.filter(
        order__gt=instance.order
    ).update(
        order=F("order") - 1
    )