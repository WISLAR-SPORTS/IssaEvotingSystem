
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .models import User, PasswordResetOTP


# =========================
# GROUP ADMIN: SUPERUSER ONLY
# =========================
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name",)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


if admin.site.is_registered(Group):
    admin.site.unregister(Group)

admin.site.register(Group, GroupAdmin)


# =========================
# PASSWORD RESET OTP ADMIN
# =========================
@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "get_email", "code", "created_at", "is_used")
    list_filter = ("is_used", "created_at")
    search_fields = ("user__username", "user__email")

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"


# =========================
# USER ADMIN FORM
# PRESERVES DJANGO PASSWORD HANDLING
# =========================
class UserAdminForm(UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        branch = cleaned_data.get("branch")
        department = cleaned_data.get("department")

        if branch and department:
            if department.branch_id != branch.id:
                raise ValidationError({
                    "department": (
                        "This department does not belong "
                        "to the selected branch."
                    )
                })

        return cleaned_data


# =========================
# CUSTOM USER ADMIN
# =========================
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):

    form = UserAdminForm

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
        "department",
    )

    # =========================
    # EDIT USER PAGE
    # =========================
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Institution Info", {
            "fields": (
                "role",
                "institution",
                "branch",
                "department",
                "student_number",
                "phone_number",
                "current_session_key",
            )
        }),
    )

    # =========================
    # ADD USER PAGE
    # =========================
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Institution Info", {
            "classes": ("wide",),
            "fields": (
                "role",
                "institution",
                "branch",
                "department",
                "student_number",
                "phone_number",
            ),
        }),
    )

    # =========================
    # QUERYSET FILTERING
    # =========================
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if request.user.role == "institution_admin":
            return qs.filter(
                institution=request.user.institution
            )

        if request.user.role == "branch_admin":
            return qs.filter(
                institution=request.user.institution,
                branch=request.user.branch,
            )

        return qs.none()

    # =========================
    # FOREIGN KEY FILTERING
    # =========================
    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if request.user.is_superuser:
            return super().formfield_for_foreignkey(
                db_field, request, **kwargs
            )

        if request.user.role == "institution_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = (
                    db_field.related_model.objects.filter(
                        id=request.user.institution_id
                    )
                )

            elif db_field.name == "branch":
                kwargs["queryset"] = (
                    db_field.related_model.objects.filter(
                        institution=request.user.institution
                    )
                )

            elif db_field.name == "department":
                kwargs["queryset"] = (
                    db_field.related_model.objects.filter(
                        branch__institution=request.user.institution
                    )
                )

        elif request.user.role == "branch_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = (
                    db_field.related_model.objects.filter(
                        id=request.user.institution_id
                    )
                )

            elif db_field.name == "branch":
                kwargs["queryset"] = (
                    db_field.related_model.objects.filter(
                        id=request.user.branch_id
                    )
                )

            elif db_field.name == "department":
                kwargs["queryset"] = (
                    db_field.related_model.objects.filter(
                        branch=request.user.branch
                    )
                )

        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    # =========================
    # ROLE RESTRICTIONS
    # =========================
    def formfield_for_choice_field(self, db_field, request, **kwargs):

        if db_field.name == "role" and not request.user.is_superuser:
            choices = list(db_field.choices)

            if request.user.role == "institution_admin":
                allowed_roles = {"branch_admin", "student"}

            elif request.user.role == "branch_admin":
                allowed_roles = {"student"}

            else:
                allowed_roles = set()

            kwargs["choices"] = [
                choice for choice in choices
                if choice[0] in allowed_roles
            ]

        return super().formfield_for_choice_field(
            db_field, request, **kwargs
        )

    # =========================
    # SAFE USER SAVING
    # =========================
    def save_model(self, request, obj, form, change):

        if request.user.is_superuser:
            pass

        elif request.user.role == "institution_admin":
            obj.institution = request.user.institution
            obj.is_superuser = False
            obj.is_staff = obj.role in {
                "institution_admin",
                "branch_admin",
            }

        elif request.user.role == "branch_admin":
            obj.institution = request.user.institution
            obj.branch = request.user.branch
            obj.is_superuser = False
            obj.is_staff = False

        super().save_model(request, obj, form, change)
