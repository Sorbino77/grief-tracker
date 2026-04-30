from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

# noqa: RUF012 — DRF serializer Meta class attributes are safe and intentional

if TYPE_CHECKING:
    from .models import User as UserType
else:
    UserType = "User"

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "department",
            "is_active",
        ]
        read_only_fields = ["id", "role", "is_active"]


class UserExportSerializer(serializers.ModelSerializer):
    """
    Full record returned by the GDPR export endpoint. Includes everything
    we store about the user, including consent timestamps but never their
    password hash.
    """
    class Meta:
        model = User
        exclude = ["password", "user_permissions", "groups"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    password2 = serializers.CharField(write_only=True, label="Confirm password")
    gdpr_consent = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text="Must be true. Records consent to the privacy notice.",
    )

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "password2",
            "first_name",
            "last_name",
            "department",
            "gdpr_consent",
        ]

    def validate_password(self, value: str) -> str:
        # Run Django\'s configured AUTH_PASSWORD_VALIDATORS (length, similarity,
        # common, numeric). Raises ValidationError on failure.
        validate_password(value)
        return value

    def validate(self, data: dict) -> dict:
        if data["password"] != data.pop("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        if not data.get("gdpr_consent"):
            raise serializers.ValidationError({
                "gdpr_consent": "You must accept the privacy notice to register.",
            })
        return data

    def create(self, validated_data: dict) -> UserType:  # type: ignore[name-defined]
        # Strip the consent flag from kwargs before user creation; record it
        # via grant_consent() so consented_at is set atomically.
        consented = validated_data.pop("gdpr_consent", False)
        user = User.objects.create_user(**validated_data)
        if consented:
            user.grant_consent()
            user.save(update_fields=["gdpr_consent", "consented_at"])
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value
