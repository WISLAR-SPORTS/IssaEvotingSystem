# institutions/models.py
from django.db import models
from django.conf import settings
from django.db import models


class Institution(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Verification"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(
        upload_to="institution_logos/",
        null=True,
        blank=True,
    )
    email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(
        max_length=30, null=True, blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_institutions",
    )
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class InstitutionScopedModel(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Branch(InstitutionScopedModel):
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("institution", "name")

    def __str__(self):
        return f"{self.name} ({self.institution.name})"


class Department(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("branch", "name")

    def __str__(self):
        return f"{self.name} ({self.branch.name} - {self.branch.institution.name})"