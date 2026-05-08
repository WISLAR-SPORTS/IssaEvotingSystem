# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from institutions.models import Institution, Branch, Department  # Import Department model
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    ROLE_CHOICES = (
        ("super_admin", "Super Admin"),
        ("institution_admin", "Institution Admin"),
        ("branch_admin", "Branch Admin"),
        ("student", "Student"),
    )

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    student_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    current_session_key = models.CharField(max_length=40, null=True, blank=True)

    institution = models.ForeignKey(
        Institution, null=True, blank=True, on_delete=models.SET_NULL
    )

    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.SET_NULL
    )

    # Add department field
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.username


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)