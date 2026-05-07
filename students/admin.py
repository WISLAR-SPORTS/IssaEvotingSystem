from django.contrib import admin
from .models import StudentRecord, StudentUpload
from core.admin_mixins import InstitutionAdminMixin
from institutions.models import Branch, Institution
from accounts.models import User
from .services.student_upload_service import process_student_upload
from django.contrib import messages


# =========================
# STUDENT RECORD ADMIN
# =========================

@admin.register(StudentRecord)
class StudentRecordAdmin(InstitutionAdminMixin, admin.ModelAdmin):

    list_display = ("id", "student_id", "name", "branch", "institution", "has_voted")
    list_filter = ("institution", "branch", "has_voted")
    search_fields = ("student_id", "name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        # Institution admin → all students in institution
        if request.user.role == "institution_admin":
            return qs.filter(institution=request.user.institution)

        # Branch admin → only their branch students
        if request.user.role == "branch_admin":
            return qs.filter(
                institution=request.user.institution,
                branch=request.user.branch
            )

        return qs.none()


# =========================
# STUDENT UPLOAD ADMIN
# =========================
from django.contrib import admin, messages
from .models import StudentUpload
from .services.student_upload_service import process_student_upload


@admin.register(StudentUpload)
class StudentUploadAdmin(InstitutionAdminMixin, admin.ModelAdmin):

    list_display = ("id", "branch", "institution", "uploaded_by", "processed", "uploaded_at")
    list_filter = ("institution", "processed")
    readonly_fields = ("processed", "uploaded_at")

    # ✅ SAVE + PROCESS FILE
    def save_model(self, request, obj, form, change):

        # re-processing
        if change and obj.processed:
            self.message_user(
                request,
                "This file has already been processed.",
                level=messages.WARNING
            )
            return

        # Auto-set fields
        if not obj.uploaded_by:
            obj.uploaded_by = request.user

        if not obj.institution:
            obj.institution = request.user.institution

        super().save_model(request, obj, form, change)

        # 🚀 PROCESS FILE
        if not obj.processed:
            try:
                errors = process_student_upload(obj)

                if errors:
                    self.message_user(
                        request,
                        f"Processed with errors: {errors}",
                        level=messages.WARNING
                    )
                else:
                    self.message_user(
                        request,
                        "Students uploaded successfully!",
                        level=messages.SUCCESS
                    )

            except Exception as e:
                self.message_user(
                    request,
                    f"Processing failed: {str(e)}",
                    level=messages.ERROR
                )

    # 🔐 LOCK FOREIGN KEYS
    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        if request.user.role == "institution_admin":

            if db_field.name == "institution":
                kwargs["queryset"] = Institution.objects.filter(
                    id=request.user.institution_id
                )

            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(
                    institution=request.user.institution
                )

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

            if db_field.name == "uploaded_by":
                kwargs["queryset"] = User.objects.filter(
                    institution=request.user.institution,
                    branch=request.user.branch
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # 🔐 LOCK QUERYSET VISIBILITY
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