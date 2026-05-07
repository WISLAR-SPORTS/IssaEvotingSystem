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
    list_display = ("id", "name", "election", "institution", "is_central")
    list_filter = ("institution", "is_central")
    search_fields = ("name",)
from django.contrib import admin
from django.db.models import Q
from .models import Candidate, Branch, User
from institutions.models import Institution


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "position", "branch", "institution")
    list_filter = ("institution", "position")
    search_fields = ("user__username",)

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        # INSTITUTION ADMIN CONTROLS
        if request.user.role == "institution_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=request.user.institution_id
                )

            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    institution=request.user.institution
                )

            if db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(
                    institution=request.user.institution
                )

        # BRANCH ADMIN CONTROLS
        if request.user.role == "branch_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=request.user.institution_id
                )

            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    id=request.user.branch_id,
                    institution=request.user.institution
                )

            if db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(
                    institution=request.user.institution,
                    branch=request.user.branch
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)