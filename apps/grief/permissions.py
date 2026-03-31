from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View


class IsManagerOrReadOnly(BasePermission):
    """Managers and admins can write; everyone else is read-only."""

    def has_permission(self, request: Request, view: View) -> bool:
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_manager)


class IsAdminOrReadOnly(BasePermission):
    """Only admins can write; authenticated users can read."""

    def has_permission(self, request: Request, view: View) -> bool:
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)
