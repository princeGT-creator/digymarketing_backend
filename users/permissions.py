from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    """
    Custom permission to only allow Super Admins to create users.
    """
    def has_permission(self, request, view):
        # Only allow creation if the user is authenticated and is a super_admin
        if view.action == "create":
            return request.user.is_authenticated and request.user.role == "super_admin"
        return True  # Allow other actions based on the default permissions
