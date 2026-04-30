from django.contrib import admin

from .models import Carrier, GriefIssue, IssueType, Location

# noqa: RUF012 — Django admin class attributes are safe and intentional


@admin.register(GriefIssue)
class GriefIssueAdmin(admin.ModelAdmin):
    list_display = [
        "kn_ref", "supplier_name", "issue_type", "carrier",
        "date", "status", "causing_party", "has_image",
    ]
    list_filter = ["status", "causing_party", "has_image", "carrier", "issue_type"]
    search_fields = ["kn_ref", "ship_id", "to_ref", "supplier_name", "note"]
    date_hierarchy = "date"
    ordering = ["-date"]
    autocomplete_fields = ["carrier", "issue_type", "location"]
    readonly_fields = ["unique_key", "created_by", "created_at", "updated_at", "resolution_days"]
    fieldsets = (
        ("Identifiers", {"fields": ("kn_ref", "ship_id", "to_ref", "unique_key")}),
        ("Supplier", {"fields": ("supplier_name", "country")}),
        ("Logistics", {"fields": ("location", "carrier")}),
        ("Issue", {"fields": ("issue_type", "date", "has_image", "causing_party", "note")}),
        ("Resolution", {"fields": ("resolve_date", "status", "resolution_days")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def resolution_days(self, obj: GriefIssue) -> int | None:
        return obj.resolution_days
    resolution_days.short_description = "Days to resolve"  # type: ignore[attr-defined]


@admin.register(IssueType)
class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "description"]
    search_fields = ["code", "description"]


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["location_code", "facility_name", "city", "country", "entity_code", "active"]
    list_filter = ["country", "active", "entity_code"]
    search_fields = ["location_code", "facility_name", "city"]
