from institutions.models import Institution, Branch
from accounts.models import User


class InstitutionAdminMixin:

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if hasattr(request.user, "institution") and request.user.institution:
            return qs.filter(institution=request.user.institution)

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        if hasattr(request.user, "institution") and request.user.institution:

            # 🔐 lock institution
            if db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=request.user.institution_id
                )

            # 🔐 lock branch
            elif db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    institution=request.user.institution
                )

            # 🔐 lock user
            elif db_field.name == "user":
                kwargs["queryset"] = User.objects.filter(
                    institution=request.user.institution
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)