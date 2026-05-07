class PermissionService:
    @staticmethod
    def is_institution_admin(user):
        return user.role == "institution_admin"

    @staticmethod
    def belongs_to_institution(user, obj):
        return user.institution_id == obj.institution_id