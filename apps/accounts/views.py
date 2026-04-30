from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserExportSerializer,
    UserSerializer,
)

# noqa: RUF012 — DRF view class attributes are safe and intentional

if TYPE_CHECKING:
    from .models import User as UserType
else:
    UserType = "User"

User = get_user_model()
audit = logging.getLogger("audit")


class RegisterView(generics.CreateAPIView):
    """
    Public endpoint — create a new account (role defaults to viewer).

    Throttled tightly: this is a common abuse target.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def perform_create(self, serializer):
        user = serializer.save()
        # Don\'t log raw emails at INFO if you have stricter PII rules; a hash
        # of the email is safer. For now we log the username (chosen by user)
        # and the new pk.
        audit.info("user_registered pk=%s username=%s", user.pk, user.username)


class TokenScopedThrottle(ScopedRateThrottle):
    """ScopedRateThrottle bound to scope="login" via TokenObtainPairView wrapper below."""
    scope_attr = "throttle_scope"


class MeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the currently authenticated user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> UserType:  # type: ignore[name-defined]
        return self.request.user  # type: ignore[return-value]

    def perform_update(self, serializer):
        user = serializer.save()
        audit.info("user_updated pk=%s", user.pk)


class DeleteMeView(APIView):
    """
    DELETE /api/v1/auth/me/

    GDPR Art. 17 — Right to erasure. We anonymise the user record (rather
    than hard-deleting) so that audit trails on issues they created remain
    intact. PII is wiped, login is disabled, ``anonymized_at`` is set.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request: Request) -> Response:
        user = request.user
        pk = user.pk
        user.anonymize()
        audit.info("user_anonymized pk=%s reason=gdpr_art17", pk)
        return Response(
            {"detail": "Your account has been anonymised. PII removed and login disabled."},
            status=status.HTTP_200_OK,
        )


class ExportMeView(APIView):
    """
    GET /api/v1/auth/me/export/

    GDPR Art. 20 — Right to data portability. Returns a JSON dump of every
    field we hold about the requesting user, plus the grief issues they
    created (their attribution).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user

        # Avoid circular import — apps.grief depends on accounts indirectly.
        from apps.grief.models import GriefIssue

        issues = GriefIssue.objects.filter(created_by=user).values(
            "id", "kn_ref", "ship_id", "to_ref", "supplier_name", "country",
            "date", "has_image", "causing_party", "resolve_date", "status",
            "note", "unique_key", "created_at", "updated_at",
        )

        audit.info("user_export pk=%s reason=gdpr_art20", user.pk)
        return Response({
            "exported_at": __import__("django").utils.timezone.now().isoformat(),
            "user": UserExportSerializer(user).data,
            "issues_created": list(issues),
        })


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            # Generic message — don\'t hint that the username is right.
            return Response(
                {"detail": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        audit.info("user_password_changed pk=%s", user.pk)
        return Response({"detail": "Password updated."})


class UserListView(generics.ListAPIView):
    """Admin-only: list all users."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
