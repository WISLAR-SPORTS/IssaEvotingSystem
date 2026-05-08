from django.contrib import admin
from .models import Institution, Branch, Department
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


@admin.register(Department)
class DepartmentAdmin(InstitutionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "branch", "branch_institution")
    list_filter = ("branch__institution", "branch")
    search_fields = ("name",)

    # Custom method to display the institution of the branch
    def branch_institution(self, obj):
        return obj.branch.institution.name
    branch_institution.short_description = "Institution"