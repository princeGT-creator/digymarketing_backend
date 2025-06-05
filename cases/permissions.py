from rest_framework import permissions

class CanViewCasePermission(permissions.BasePermission):
    """
    Custom permission to allow:
    - super_admin and admin to view all cases
    - internal users to view only assigned cases
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in ['super_admin', 'admin', 'external_lawyer']:
            return True
    
        if user.role == "customer":
            return True

        # Assuming `assigned_to` is a FK to User on the Case model
        return obj.lawyer == user

    def has_permission(self, request, view):
        # Needed so list view doesn't block internal users
        return True


class CanCreateCasePermission(permissions.BasePermission):
    """
    Permission to:
    - Allow only super_admin, admin, and external users to create cases
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method == 'POST':
            return user.role in ['super_admin', 'admin', 'external_lawyer']
        return True

class RevisionCasePermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in ['super_admin', 'admin']:
            return True

        return False

    def has_permission(self, request, view):
        user = request.user
        if user.role in ['super_admin', 'admin']:
            return True

        return False