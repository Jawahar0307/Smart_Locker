"""
Custom permissions for role-based access control.
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdmin(BasePermission):
    """
    Permission that allows access only to users with admin role.
    """

    message = 'Admin access required.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Permission that allows access to the resource owner or admin users.
    """

    message = 'You do not have permission to access this resource.'

    def has_object_permission(
        self, request: Request, view: APIView, obj: object
    ) -> bool:
        if request.user.role == 'admin':
            return True
        # Check if the object has a 'user' attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user
