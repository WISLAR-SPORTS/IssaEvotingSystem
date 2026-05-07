# institutions/models.py
from django.db import models
class Institution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to="institution_logos/", null=True, blank=True)

    # 🆕 Contact fields
    email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=30, null=True, blank=True)

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