from django.contrib import admin
from core.admin_mixins import InstitutionAdminMixin
from .models import Election, Position, Candidate
from core.branchadmin_mixin import BranchAdminMixin



@admin.register(Election)
class ElectionAdmin(InstitutionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "institution", "start_time", "end_time")
    list_filter = ("institution",)
    search_fields = ("name",)

@admin.register(Position)
class PositionAdmin(InstitutionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "election", "institution", "is_central", "department", "branch")
    list_filter = ("institution", "is_central", "department")
    search_fields = ("name",)
from django.contrib import admin
from django.db.models import Q
from .models import Candidate, Branch, User
from institutions.models import Institution

from django.contrib import admin
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Candidate
from institutions.models import Institution, Branch, Department
from accounts.models import User


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "position", "branch", "institution")
    list_filter = ("institution", "position", "branch")
    search_fields = ("user__username",)

    # =========================
    # QUERYSET FILTERING
    # =========================
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        # Institution admin → all candidates in institution
        if request.user.role == "institution_admin":
            return qs.filter(institution=request.user.institution)

        # Branch admin → their branch + central candidates
        if request.user.role == "branch_admin":
            return qs.filter(
                institution=request.user.institution
            ).filter(
                Q(branch=request.user.branch) |
                Q(position__is_central=True)
            )

        return qs.none()

    # =========================
    # FOREIGN KEY FILTERING
    # =========================
    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        user = request.user

        # =====================
        # INSTITUTION ADMIN
        # =====================
        if user.role == "institution_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=user.institution_id
                )

            elif db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    institution=user.institution
                )

            elif db_field.name == "department":
                kwargs["queryset"] = Department.objects.filter(
                    branch__institution=user.institution
                )

            elif db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(
                    institution=user.institution
                )

        # =====================
        # BRANCH ADMIN
        # =====================
        elif user.role == "branch_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=user.institution_id
                )

            elif db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    id=user.branch_id,
                    institution=user.institution
                )

            elif db_field.name == "department":
                kwargs["queryset"] = Department.objects.filter(
                    branch=user.branch
                )

            elif db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(
                    institution=user.institution,
                    branch=user.branch
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # =========================
    # 🔐 VALIDATION (IMPORTANT FIX)
    # =========================
    def clean(self):
        """
        Prevent:
        - cross-branch department selection
        - invalid branch-department mismatch
        """
        cleaned_data = super().clean()

        branch = cleaned_data.get("branch")
        department = cleaned_data.get("department")

        if branch and department:
            if department.branch_id != branch.id:
                raise ValidationError({
                    "department": "This department does not belong to the selected branch."
                })

        return cleaned_data