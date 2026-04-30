from rest_framework import serializers

from .models import Carrier, GriefIssue, IssueType, Location


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ["id", "code", "description"]


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = ["id", "name"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id", "location_code", "facility_name", "entity_code",
            "city", "country", "active", "delivery_group",
        ]


class GriefIssueListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    carrier: serializers.Field = serializers.StringRelatedField()
    issue_type: serializers.Field = serializers.StringRelatedField()
    location: serializers.Field = serializers.StringRelatedField()
    resolution_days = serializers.ReadOnlyField()

    class Meta:
        model = GriefIssue
        fields = [
            "id", "kn_ref", "ship_id", "to_ref", "supplier_name", "country",
            "location", "carrier", "issue_type", "date", "has_image",
            "causing_party", "resolve_date", "status", "resolution_days",
            "created_at",
        ]


class GriefIssueDetailSerializer(serializers.ModelSerializer):
    """Full serializer for create / retrieve / update."""
    carrier_detail = CarrierSerializer(source="carrier", read_only=True)
    issue_type_detail = IssueTypeSerializer(source="issue_type", read_only=True)
    location_detail = LocationSerializer(source="location", read_only=True)
    resolution_days = serializers.ReadOnlyField()

    # Accept FK by name/id on write
    carrier = serializers.PrimaryKeyRelatedField(
        queryset=Carrier.objects.all(), allow_null=True, required=False,
    )
    issue_type = serializers.PrimaryKeyRelatedField(
        queryset=IssueType.objects.all(), allow_null=True, required=False,
    )
    location = serializers.SlugRelatedField(
        queryset=Location.objects.all(), slug_field="location_code",
        allow_null=True, required=False,
    )

    class Meta:
        model = GriefIssue
        fields = [
            "id", "kn_ref", "ship_id", "to_ref", "supplier_name", "country",
            "location", "location_detail",
            "carrier", "carrier_detail",
            "issue_type", "issue_type_detail",
            "date", "has_image", "causing_party",
            "resolve_date", "status", "note",
            "resolution_days", "unique_key",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "unique_key", "created_by", "created_at", "updated_at"]
