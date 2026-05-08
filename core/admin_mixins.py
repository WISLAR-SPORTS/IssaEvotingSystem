from institutions.models import Institution, Branch
from accounts.models import User


class InstitutionAdminMixin:

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # SUPERADMIN → everything
        if request.user.is_superuser:
            return qs

        model_fields = [field.name for field in qs.model._meta.fields]

        # =========================
        # INSTITUTION ADMIN
        # =========================
        if request.user.role == "institution_admin":

            # Models with direct institution field
            if "institution" in model_fields:
                return qs.filter(
                    institution=request.user.institution
                )

            # Models connected through branch
            elif "branch" in model_fields:
                return qs.filter(
                    branch__institution=request.user.institution
                )

        # =========================
        # BRANCH ADMIN
        # =========================
        if request.user.role == "branch_admin":

            # Models with branch field
            if "branch" in model_fields:
                return qs.filter(
                    branch=request.user.branch
                )

            # Models with institution field
            elif "institution" in model_fields:
                return qs.filter(
                    institution=request.user.institution
                )

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        # SUPERADMIN → unrestricted
        if request.user.is_superuser:
            return super().formfield_for_foreignkey(
                db_field, request, **kwargs
            )

        # =========================
        # INSTITUTION ADMIN
        # =========================
        if request.user.role == "institution_admin":

            # Institution selector
            if db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=request.user.institution_id
                )

            # Branch selector
            elif db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    institution=request.user.institution
                )

            # User selector
            elif db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(
                    institution=request.user.institution
                )

        # =========================
        # BRANCH ADMIN
        # =========================
        elif request.user.role == "branch_admin":

            # Restrict branch to only theirs
            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    id=request.user.branch_id
                )

            # Restrict institution
            elif db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=request.user.institution_id
                )

            # Restrict users
            elif db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(
                    branch=request.user.branch
                )

        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )