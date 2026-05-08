# voting/models.py
from django.db import models
from django.core.exceptions import ValidationError
from institutions.models import InstitutionScopedModel, Branch, Department  # Import Department
from accounts.models import User
from elections.models import Candidate, Position, Election


class VotingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Vote(InstitutionScopedModel):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    department = models.ForeignKey(  # Added department field
        Department, null=True, blank=True, on_delete=models.SET_NULL
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("voter", "position")

        indexes = [
            models.Index(fields=["institution"]),
            models.Index(fields=["position"]),
            models.Index(fields=["candidate"]),
            models.Index(fields=["department"]),  # Added index for department
        ]

    def clean(self):
        # same institution
        if self.voter.institution != self.institution:
            raise ValidationError("Voter must belong to the same institution")

        # branch check
        if self.voter.branch != self.branch:
            raise ValidationError("Voter must belong to the selected branch")

        # department check
        if self.department and self.voter.department != self.department:
            raise ValidationError("Voter must belong to the selected department")

        # candidate position match
        if self.candidate.position != self.position:
            raise ValidationError("Candidate does not match position")

        # branch vs central logic
        if not self.position.is_central:
            if self.candidate.branch != self.branch:
                raise ValidationError("Candidate must belong to the same branch")

    def __str__(self):
        return f"{self.voter} -> {self.candidate}"