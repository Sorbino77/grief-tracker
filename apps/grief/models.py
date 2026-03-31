from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# ── Reference tables (from Formulas sheet) ────────────────────────────────────

class IssueType(models.Model):
    code = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Issue Type"

    def __str__(self) -> str:
        return self.code


class CausingParty(models.TextChoices):
    SUPPLIER = "SUPPLIER", "Supplier"
    CARRIER = "CARRIER", "Carrier"
    MIXED = "MIXED", "Mixed"


class IssueStatus(models.TextChoices):
    SOLVED = "SOLVED", "Solved"
    ONGOING = "ONGOING", "Ongoing"


class Carrier(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Location(models.Model):
    """Mirrors the Loc Codes sheet."""
    facility = models.CharField(max_length=200)
    entity_code = models.CharField(max_length=10, blank=True)
    location_code = models.CharField(max_length=20, unique=True)
    facility_name = models.CharField(max_length=200, blank=True)
    street = models.CharField(max_length=200, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=5, blank=True)
    active = models.BooleanField(default=True)
    delivery_group = models.CharField(max_length=5, blank=True)
    broker_name = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["location_code"]

    def __str__(self) -> str:
        return f"{self.location_code} — {self.city}"


# ── Core model ────────────────────────────────────────────────────────────────

class GriefIssue(models.Model):
    # Identifiers (from Excel: K&N REF, Ship ID, TO Ref)
    kn_ref = models.CharField(max_length=50, db_index=True)
    ship_id = models.CharField(max_length=50, blank=True, db_index=True)
    to_ref = models.CharField(max_length=50, blank=True)

    # Supplier
    supplier_name = models.CharField(max_length=200, blank=True, db_index=True)
    country = models.CharField(max_length=5, blank=True)

    # Logistics
    location = models.ForeignKey(
        Location,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="issues",
        to_field="location_code",
    )
    carrier = models.ForeignKey(
        Carrier,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="issues",
    )

    # Issue details
    issue_type = models.ForeignKey(
        IssueType,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="issues",
        to_field="code",
    )
    date = models.DateField(db_index=True)
    has_image = models.BooleanField(default=False)
    causing_party = models.CharField(
        max_length=20,
        choices=CausingParty.choices,
        blank=True,
    )

    # Resolution
    resolve_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=IssueStatus.choices,
        default=IssueStatus.ONGOING,
        db_index=True,
    )
    note = models.TextField(blank=True)

    # Deduplication key from Excel
    unique_key = models.CharField(max_length=200, unique=True, blank=True)

    # Audit
    created_by = models.ForeignKey(
        User,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="created_issues",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = "Grief Issue"
        verbose_name_plural = "Grief Issues"
        indexes = [
            models.Index(fields=["status", "date"]),
            models.Index(fields=["carrier", "date"]),
            models.Index(fields=["issue_type", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.kn_ref} — {self.issue_type} ({self.status})"

    def save(self, *args, **kwargs) -> None:
        # Build unique_key same way Excel did: kn_ref + issue_type
        if not self.unique_key and self.kn_ref:
            issue_code = self.issue_type.code if self.issue_type else ""
            self.unique_key = f"{self.kn_ref}{issue_code}"
        super().save(*args, **kwargs)

    @property
    def resolution_days(self) -> int | None:
        if self.resolve_date and self.date:
            return (self.resolve_date - self.date).days
        return None
