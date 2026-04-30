from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    ChangePasswordView,
    DeleteMeView,
    ExportMeView,
    MeView,
    RegisterView,
    UserListView,
)


# Wrap SimpleJWT views to add per-endpoint throttling without subclassing them.
class _ThrottledTokenObtainPairView(TokenObtainPairView):
    """Login: 10/min per IP. Slows brute force without locking out real users."""
    throttle_scope = "login"
    throttle_classes = [
        __import__("rest_framework").throttling.ScopedRateThrottle,
    ]


class _ThrottledTokenRefreshView(TokenRefreshView):
    """Refresh: same 10/min cap. Caller hits this on token expiry."""
    throttle_scope = "login"
    throttle_classes = [
        __import__("rest_framework").throttling.ScopedRateThrottle,
    ]


urlpatterns = [
    # JWT
    path("token/", _ThrottledTokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", _ThrottledTokenRefreshView.as_view(), name="token-refresh"),

    # Account self-service
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change-password"),

    # GDPR rights
    path("me/delete/", DeleteMeView.as_view(), name="me-delete"),         # Art. 17
    path("me/export/", ExportMeView.as_view(), name="me-export"),         # Art. 20

    # Admin
    path("users/", UserListView.as_view(), name="user-list"),
]
