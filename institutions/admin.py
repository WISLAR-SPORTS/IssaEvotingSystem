from django.contrib import admin
from .models import Institution, Branch
from core.admin_mixins import InstitutionAdminMixin



@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(Branch)
class BranchAdmin(InstitutionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "institution")
    list_filter = ("institution",)
    search_fields = ("name",)