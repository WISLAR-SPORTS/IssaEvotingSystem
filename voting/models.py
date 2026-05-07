# voting/models.py
from django.db import models
from django.core.exceptions import ValidationError
from institutions.models import InstitutionScopedModel, Branch
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

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("voter", "position")

        indexes = [
            models.Index(fields=["institution"]),
            models.Index(fields=["position"]),
            models.Index(fields=["candidate"]),
        ]

    def clean(self):
        # same institution
        if self.voter.institution != self.institution:
            raise ValidationError("Voter must belong to same institution")

        # branch check
        if self.voter.branch != self.branch:
            raise ValidationError("Voter must belong to the selected branch")

        # candidate position match
        if self.candidate.position != self.position:
            raise ValidationError("Candidate does not match position")

        # branch vs central logic
        if not self.position.is_central:
            if self.candidate.branch != self.branch:
                raise ValidationError("Candidate must belong to same branch")

    def __str__(self):
        return f"{self.voter} -> {self.candidate}"