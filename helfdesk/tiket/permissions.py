from rest_framework.permissions import BasePermission

class IsAdminDeleteOnly(BasePermission):
    def has_permission(self, request, view):
        # Allow everyone to view or create
        if request.method in ['GET', 'POST', 'PUT', 'PATCH']:
            return True

        # Only admin can delete
        if request.method == 'DELETE':
            return request.user.is_superuser

        return False