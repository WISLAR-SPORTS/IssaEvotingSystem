from django.contrib import admin
from .models import Institution, Branch, Department
from core.admin_mixins import InstitutionAdminMixin


from django.contrib import admin
from django.utils import timezone

from .models import Institution
from accounts.models import User


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "contact_phone",
        "status",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "contact_phone")

    actions = ["approve_institutions", "reject_institutions"]

    @admin.action(description="Approve selected institutions")
    def approve_institutions(self, request, queryset):
        for institution in queryset:
            institution.status = "approved"
            institution.reviewed_at = timezone.now()
            institution.reviewed_by = request.user
            institution.rejection_reason = ""
            institution.save()

            User.objects.filter(
                institution=institution,
                role="institution_admin",
            ).update(is_active=True)

    @admin.action(description="Reject selected institutions")
    def reject_institutions(self, request, queryset):
        for institution in queryset:
            institution.status = "rejected"
            institution.reviewed_at = timezone.now()
            institution.reviewed_by = request.user
            institution.save()

            User.objects.filter(
                institution=institution,
                role="institution_admin",
            ).update(is_active=False)


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