from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Module


def renumber_orders():
    qs = (
        Module.objects
        .exclude(order__isnull=True)
        .order_by("order", "id")
        .only("id", "order")
    )
    with transaction.atomic():
        for i, m in enumerate(qs, start=1):
            if m.order != i:
                Module.objects.filter(pk=m.pk).update(order=i)


@receiver(post_delete, sender=Module)
def renumber_on_delete(sender, instance, **kwargs):
    renumber_orders()


@receiver(post_save, sender=Module)
def renumber_on_save(sender, instance, created, **kwargs):
    renumber_orders()
