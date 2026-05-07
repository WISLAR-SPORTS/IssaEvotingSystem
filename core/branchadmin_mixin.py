from django.db.models import Q


class BranchAdminMixin:

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if request.user.role == "branch_admin":
            return qs.filter(
                institution=request.user.institution
            ).filter(
                Q(branch=request.user.branch) |
                Q(position__is_central=True)
            )

        if request.user.role == "institution_admin":
            return qs.filter(institution=request.user.institution)

        return qs.none()