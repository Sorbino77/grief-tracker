import django_filters
from .models import GriefIssue


class GriefIssueFilter(django_filters.FilterSet):
    # Date range
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    # Text lookups
    supplier = django_filters.CharFilter(field_name="supplier_name", lookup_expr="icontains")
    note = django_filters.CharFilter(lookup_expr="icontains")

    # FK filters by name
    carrier_name = django_filters.CharFilter(field_name="carrier__name", lookup_expr="iexact")
    issue_code = django_filters.CharFilter(field_name="issue_type__code", lookup_expr="iexact")
    location_code = django_filters.CharFilter(field_name="location__location_code", lookup_expr="iexact")

    # Enum / choice filters
    status = django_filters.CharFilter(lookup_expr="iexact")
    causing_party = django_filters.CharFilter(lookup_expr="iexact")
    country = django_filters.CharFilter(lookup_expr="iexact")
    has_image = django_filters.BooleanFilter()

    # Year / month shortcuts
    year = django_filters.NumberFilter(field_name="date", lookup_expr="year")
    month = django_filters.NumberFilter(field_name="date", lookup_expr="month")

    class Meta:
        model = GriefIssue
        fields = [
            "date_from", "date_to",
            "carrier_name", "issue_code", "location_code",
            "status", "causing_party", "country", "has_image",
            "year", "month",
            "supplier", "note",
        ]
