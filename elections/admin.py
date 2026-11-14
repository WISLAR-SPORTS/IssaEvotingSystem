from django.contrib import admin
from core.admin_mixins import InstitutionAdminMixin
from .models import Election, Position, Candidate
from core.branchadmin_mixin import BranchAdminMixin


from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils import timezone

from .models import Election, Position, Candidate
from institutions.admin import InstitutionAdminMixin


@admin.register(Election)
class ElectionAdmin(InstitutionAdminMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "institution",
        "start_time",
        "end_time",
    )

    list_filter = ("institution",)
    search_fields = ("name",)

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "live-results/",
                self.admin_site.admin_view(self.live_results_view),
                name="elections_live_results",
            ),
        ]

        return custom_urls + urls

    def live_results_view(self, request):
        institution = getattr(request.user, "institution", None)
        now = timezone.now()

        elections = Election.objects.none()
        results = []

        if institution:
            elections = Election.objects.filter(
                institution=institution,
                start_time__lte=now,
                end_time__gte=now,
            )

            for election in elections:
                positions = Position.objects.filter(
                    election=election,
                    institution=institution,
                ).select_related(
                    "branch",
                    "department",
                )

                for position in positions:
                    candidates = Candidate.objects.filter(
                        position=position,
                        institution=institution,
                    ).select_related(
                        "user",
                        "branch",
                        "department",
                    )

                    results.append({
                        "election": election,
                        "position": position,
                        "candidates": candidates,
                    })

        context = {
            **self.admin_site.each_context(request),
            "title": "Live Election Results",
            "institution": institution,
            "elections": elections,
            "results": results,
        }

        return render(
            request,
            "admin/elections/live_results.html",
            context,
        )
    

from django.contrib import admin
from django.utils import timezone

from django.contrib import admin
from django.utils import timezone

from .models import Position, Election
from students.models import Branch
from institutions.models import Department


@admin.register(Position)
class PositionAdmin(InstitutionAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "election",
        "institution",
        "is_central",
        "department",
        "branch",
    )

    list_filter = (
        "institution",
        "is_central",
        "department",
        "branch",
    )

    search_fields = ("name",)

    def get_user_institution(self, request):
        """Resolve the logged-in user's institution."""
        institution = getattr(request, "institution", None)

        if institution is None:
            institution = getattr(request.user, "institution", None)

        if institution is None:
            profile = getattr(request.user, "profile", None)
            if profile is not None:
                institution = getattr(profile, "institution", None)

        return institution

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        institution = self.get_user_institution(request)

        if db_field.name == "election":
            if institution is not None:
                now = timezone.now()
                kwargs["queryset"] = Election.objects.filter(
                    institution=institution,
                    start_time__lte=now,
                    end_time__gte=now,
                )
            else:
                kwargs["queryset"] = Election.objects.none()

        elif db_field.name == "branch":
            if institution is not None:
                kwargs["queryset"] = Branch.objects.filter(
                    institution=institution
                )
            else:
                kwargs["queryset"] = Branch.objects.none()

        elif db_field.name == "department":
            if institution is not None:
                kwargs["queryset"] = Department.objects.filter(
                    branch__institution=institution
                ).distinct()
            else:
                kwargs["queryset"] = Department.objects.none()

        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    def save_model(self, request, obj, form, change):
        """Prevent assigning a position to another institution."""
        institution = self.get_user_institution(request)

        if institution is None:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                "Your account has no institution assigned."
            )

        # Ensure the position belongs to the logged-in user's institution.
        obj.institution = institution

        # Validate related objects even if a request bypasses the dropdown.
        if obj.branch_id and obj.branch.institution_id != institution.id:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                "You cannot select a branch from another institution."
            )

        if (
            obj.department_id
            and obj.department.branch.institution_id != institution.id
        ):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                "You cannot select a department from another institution."
            )

        if obj.election.institution_id != institution.id:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                "You cannot select an election from another institution."
            )

        super().save_model(request, obj, form, change)

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