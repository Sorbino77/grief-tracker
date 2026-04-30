from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import GriefIssueFilter
from .models import Carrier, GriefIssue, IssueType, Location
from .permissions import IsAdminOrReadOnly, IsManagerOrReadOnly
from .serializers import (
    CarrierSerializer,
    GriefIssueDetailSerializer,
    GriefIssueListSerializer,
    IssueTypeSerializer,
    LocationSerializer,
)

# ── GriefIssue ────────────────────────────────────────────────────────────────

class GriefIssueListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/grief/issues/   — paginated, filterable list
    POST /api/v1/grief/issues/   — create a new issue (managers+)
    """
    queryset = (
        GriefIssue.objects
        .select_related("carrier", "issue_type", "location", "created_by")
        .all()
    )
    filterset_class = GriefIssueFilter
    search_fields = ["kn_ref", "ship_id", "to_ref", "supplier_name", "note"]
    ordering_fields = ["date", "resolve_date", "status", "supplier_name", "kn_ref"]
    ordering = ["-date"]
    permission_classes = [IsManagerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GriefIssueDetailSerializer
        return GriefIssueListSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(created_by=self.request.user)


class GriefIssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/grief/issues/<pk>/
    PATCH  /api/v1/grief/issues/<pk>/
    DELETE /api/v1/grief/issues/<pk>/  (admin only)
    """
    queryset = GriefIssue.objects.select_related("carrier", "issue_type", "location", "created_by")
    serializer_class = GriefIssueDetailSerializer
    permission_classes = [IsManagerOrReadOnly]

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        if not request.user or not request.user.is_authenticated or not request.user.is_admin:  # type: ignore[union-attr]
            return Response(
                {"detail": "Only admins can delete issues."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


# ── Reference data (read-only for all authenticated users) ────────────────────

class IssueTypeListView(generics.ListCreateAPIView):
    queryset = IssueType.objects.all()
    serializer_class = IssueTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["code", "description"]


class IssueTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IssueType.objects.all()
    serializer_class = IssueTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class CarrierListView(generics.ListCreateAPIView):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]


class CarrierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [IsAdminOrReadOnly]


class LocationListView(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["location_code", "facility_name", "city"]
    filterset_fields = ["country", "active", "entity_code"]
    ordering_fields = ["location_code", "city"]


class LocationDetailView(generics.RetrieveUpdateAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "location_code"
