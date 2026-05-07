# elections/models.py
from django.db import models
from institutions.models import InstitutionScopedModel, Branch
from accounts.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Election(InstitutionScopedModel):
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    

    def __str__(self):
        return self.name
   
        


class Position(InstitutionScopedModel):
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    # KEY FIELD
    is_central = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.election.name})"
    class Meta:
     unique_together = ('election', 'name')
from django.core.exceptions import ValidationError

class Candidate(InstitutionScopedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="candidate_images/", null=True, blank=True)


    def clean(self):
        if self.position.is_central:
            if self.branch is not None:
                raise ValidationError("Central candidates should not have a branch")
        else:
            if self.branch is None:
                raise ValidationError("Branch candidates must belong to a branch")

    def save(self, *args, **kwargs):
        self.full_clean()  # ALWAYS run validation
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.user.first_name} - {self.user.last_name}"