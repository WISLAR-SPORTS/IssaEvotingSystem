from django.contrib import admin
from .models import AuditLog
from core.admin_mixins import InstitutionAdminMixin


@admin.register(AuditLog)
class AuditLogAdmin(InstitutionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "user", "action", "model_name", "object_id", "timestamp")
    list_filter = ("model_name", "timestamp")
    search_fields = ("action",)