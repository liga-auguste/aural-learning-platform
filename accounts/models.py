from django.contrib.auth.models import AbstractUser
from django.db import models


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