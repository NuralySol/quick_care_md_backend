from rest_framework import permissions

# This is a custom permission class that allows only admins to edit or delete, but read access is allowed to all.

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only admins to edit or delete, but read access is allowed to all.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'

class IsDoctorUser(permissions.BasePermission):
    """
    Custom permission to allow only doctors to perform actions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'