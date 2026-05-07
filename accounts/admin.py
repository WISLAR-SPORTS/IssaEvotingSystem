from django.contrib import admin
from .models import User
from core.admin_mixins import InstitutionAdminMixin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core.branchadmin_mixin import BranchAdminMixin


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetOTP


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "get_email", "code", "created_at", "is_used")
    list_filter = ("is_used", "created_at")

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):

    list_display = (
        "username",
        "email",
        "student_number",
        "current_session_key",
        "phone_number",
        "first_name",
        "last_name",
        "role",
        "institution",
        "branch",
    )

    # ✅ EDIT USER PAGE
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Institution Info", {
            "fields": (
                "role",
                "institution",
                "branch",
                "student_number",
                "phone_number",
                "current_session_key",
            )
        }),
    )

    # ✅ ADD USER PAGE (THIS WAS MISSING)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Institution Info", {
            "classes": ("wide",),
            "fields": (
                "role",
                "institution",
                "branch",
                "student_number",
                "phone_number",
            ),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if request.user.role == "institution_admin":
            return qs.filter(institution=request.user.institution)

        if request.user.role == "branch_admin":
            return qs.filter(
                institution=request.user.institution,
                branch=request.user.branch
            )

        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if request.user.is_superuser:
            return super().formfield_for_foreignkey(
                db_field,
                request,
                **kwargs
            )

        # Institution admin scope
        if request.user.role == "institution_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    id=request.user.institution_id
                )

        # Branch admin scope
        if request.user.role == "branch_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    id=request.user.institution_id
                )

            if db_field.name == "branch":
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    id=request.user.branch_id
                )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs
        )