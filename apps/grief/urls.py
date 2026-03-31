from django.urls import path

from .views import (
    CarrierDetailView,
    CarrierListView,
    GriefIssueDetailView,
    GriefIssueListCreateView,
    IssueTypeDetailView,
    IssueTypeListView,
    LocationDetailView,
    LocationListView,
)

urlpatterns = [
    # Issues
    path("issues/", GriefIssueListCreateView.as_view(), name="issue-list"),
    path("issues/<int:pk>/", GriefIssueDetailView.as_view(), name="issue-detail"),
    # Reference data
    path("issue-types/", IssueTypeListView.as_view(), name="issue-type-list"),
    path("issue-types/<int:pk>/", IssueTypeDetailView.as_view(), name="issue-type-detail"),
    path("carriers/", CarrierListView.as_view(), name="carrier-list"),
    path("carriers/<int:pk>/", CarrierDetailView.as_view(), name="carrier-detail"),
    path("locations/", LocationListView.as_view(), name="location-list"),
    path("locations/<str:location_code>/", LocationDetailView.as_view(), name="location-detail"),
]
