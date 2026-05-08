# students/models.py
from django.db import models
from institutions.models import InstitutionScopedModel, Branch, Department  # Import Department
from accounts.models import User


class StudentRecord(InstitutionScopedModel):
    student_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    # Add department field
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )

    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    has_voted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.student_id})"


class StudentUpload(InstitutionScopedModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    # Add department field
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )

    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    file = models.FileField(upload_to="student_uploads/")
    processed = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)