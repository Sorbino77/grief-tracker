from django.urls import path

from .views import (
    ByCarrierView,
    ByCausingPartyView,
    ByIssueTypeView,
    ByLocationView,
    ByMonthView,
    KPISummaryView,
)

urlpatterns = [
    path("kpi/", KPISummaryView.as_view(), name="kpi-summary"),
    path("by-carrier/", ByCarrierView.as_view(), name="by-carrier"),
    path("by-issue-type/", ByIssueTypeView.as_view(), name="by-issue-type"),
    path("by-causing-party/", ByCausingPartyView.as_view(), name="by-causing-party"),
    path("by-month/", ByMonthView.as_view(), name="by-month"),
    path("by-location/", ByLocationView.as_view(), name="by-location"),
]
