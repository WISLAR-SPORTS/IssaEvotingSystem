from django.contrib import admin
from .models import Vote, VotingSession
from core.admin_mixins import InstitutionAdminMixin


@admin.register(VotingSession)
class VotingSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "election", "is_active", "created_at")
    list_filter = ("is_active", "election")


@admin.register(Vote)
class VoteAdmin(InstitutionAdminMixin, admin.ModelAdmin):
    list_display = ("id", "voter", "candidate", "position", "branch", "institution", "timestamp")
    list_filter = ("institution", "position", "branch")
    search_fields = ("voter__username",)

    # IMPORTANT: prevent manual tampering
    def has_add_permission(self, request):
        return False