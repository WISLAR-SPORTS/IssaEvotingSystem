# audit/models.py
from django.db import models
from accounts.models import User


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=255)

    model_name = models.CharField(max_length=255)
    object_id = models.IntegerField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.model_name}"