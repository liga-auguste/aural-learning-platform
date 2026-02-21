# accounts/signals.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

TEACHER_GROUP = "Lehrer"
STUDENT_GROUP = "Schüler"

@receiver(post_save, sender=User)
def sync_role_to_groups(sender, instance, **kwargs):
    """
    Synchronisiert role -> Gruppen:
    - TEACHER: in Gruppe 'Lehrer', nicht in 'Schüler'
    - STUDENT: in Gruppe 'Schüler', nicht in 'Lehrer'
    - Superuser bleibt immer is_staff=True
    """

    teacher_group, _ = Group.objects.get_or_create(name=TEACHER_GROUP)
    student_group, _ = Group.objects.get_or_create(name=STUDENT_GROUP)

    # --- Superuser-Absicherung ---
    if instance.is_superuser:
        # Superuser soll IMMER Staff bleiben
        if not instance.is_staff:
            User.objects.filter(pk=instance.pk).update(is_staff=True)
    # --- Ende Absicherung ---


    if instance.role == instance.TEACHER:
        # Gruppen setzen
        instance.groups.add(teacher_group)
        instance.groups.remove(student_group)

        # Teacher darf in den Admin -> is_staff True
        if not instance.is_staff:
            User.objects.filter(pk=instance.pk).update(is_staff=True)

    else:
        # Default: STUDENT
        instance.groups.add(student_group)
        instance.groups.remove(teacher_group)

        # Student soll nicht in den Admin (aber NIE Superuser anfassen!)
        if instance.is_staff and not instance.is_superuser:
            User.objects.filter(pk=instance.pk).update(is_staff=False)