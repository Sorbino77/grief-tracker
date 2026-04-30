from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# noqa: RUF012 — Django model Meta class attributes are safe and intentional


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        OPERATOR = "operator", "Operator"
        VIEWER = "viewer", "Viewer"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    department = models.CharField(max_length=100, blank=True)

    # ── GDPR ─────────────────────────────────────────────────────────────────
    # We require explicit consent at registration. consented_at is the legal
    # evidence of when consent was given (Art. 7 GDPR — burden of proof).
    gdpr_consent = models.BooleanField(
        default=False,
        help_text="User has accepted the privacy notice. Required at registration.",
    )
    consented_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp at which gdpr_consent was set to True.",
    )

    # Right to erasure (Art. 17): rather than deleting the row (which would
    # cascade-null FK-set issues created_by to NULL and lose audit trail),
    # we anonymise PII and mark the account inactive.
    anonymized_at = models.DateTimeField(
        null=True, blank=True,
        help_text="If set, this account was anonymised under GDPR Art. 17.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["email"]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role in (self.Role.ADMIN, self.Role.MANAGER)

    def grant_consent(self) -> None:
        """Record that the user has accepted the privacy notice."""
        self.gdpr_consent = True
        self.consented_at = timezone.now()

    def anonymize(self) -> None:
        """
        GDPR Art. 17 right to erasure, implemented via anonymisation.

        We keep the row (so audit trails like ``GriefIssue.created_by`` survive)
        but strip PII and disable login. The original email is replaced with a
        deterministic non-PII placeholder.
        """
        marker = f"deleted-user-{self.pk}@anonymized.invalid"
        self.email = marker
        self.username = f"deleted-user-{self.pk}"
        self.first_name = ""
        self.last_name = ""
        self.department = ""
        self.is_active = False
        self.set_unusable_password()
        self.anonymized_at = timezone.now()
        self.save()
