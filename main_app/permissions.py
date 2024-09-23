from rest_framework import permissions

# This is a custom permission class that allows only admins to edit or delete, but read access is allowed to all.

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow:
    - Admins to edit or delete patients in their Admin panel.
    """
    def has_permission(self, request, view):
        # Safe methods like GET, HEAD, OPTIONS are allowed for everyone.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # If the user is authenticated and is an admin, they can perform any action.
        return request.user.is_authenticated and (request.user.role == 'admin' or request.user.role == 'doctor')

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admins have full access
        if request.user.role == 'admin':
            return True
        
        # Doctors can modify only their own patients
        if request.user.role == 'doctor' and obj.doctor == request.user.doctor:
            return True

        return False

class IsDoctorUser(permissions.BasePermission):
    """
    Custom permission to allow only doctors to perform actions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'
    
from rest_framework import permissions

class IsAdminWithRole(permissions.BasePermission):
    """
    Custom permission to check if the user is both a staff and has the 'admin' role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff and request.user.role == 'admin'