from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsManagerOrReadOnly(BasePermission):
    """Managers and admins can write; everyone else is read-only."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_manager)


class IsAdminOrReadOnly(BasePermission):
    """Only admins can write; authenticated users can read."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)
