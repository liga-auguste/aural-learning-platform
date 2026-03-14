import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"

    ROLE_CHOICES = [
        (TEACHER, "Lehrkraft"),
        (STUDENT, "Schüler"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=STUDENT,
    )

    @property
    def is_teacher(self):
        return self.role == self.TEACHER

    @property
    def is_student(self):
        return self.role == self.STUDENT

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class InviteToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.STUDENT)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_invites"
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Einladung ({self.get_role_display()}) von {self.created_by} – {'verwendet' if self.used else 'offen'}"