from django.db.models import Avg, Count, F, FloatField, Q
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grief.models import GriefIssue, IssueStatus


def _base_qs(request: Request):
    """Apply common query-string filters to any queryset."""
    qs = GriefIssue.objects.all()
    p = request.query_params
    if year := p.get("year"):
        qs = qs.filter(date__year=year)
    if month := p.get("month"):
        qs = qs.filter(date__month=month)
    if carrier := p.get("carrier"):
        qs = qs.filter(carrier__name__iexact=carrier)
    if issue_type := p.get("issue_type"):
        qs = qs.filter(issue_type__code__iexact=issue_type)
    if causing_party := p.get("causing_party"):
        qs = qs.filter(causing_party__iexact=causing_party)
    if date_from := p.get("date_from"):
        qs = qs.filter(date__gte=date_from)
    if date_to := p.get("date_to"):
        qs = qs.filter(date__lte=date_to)
    return qs


class KPISummaryView(APIView):
    """
    GET /api/v1/analytics/kpi/
    Returns overall totals — mirrors the header stats in the Grief sheet.
    Supports filters: year, month, carrier, issue_type, causing_party, date_from, date_to
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = _base_qs(request)
        total = qs.count()
        solved = qs.filter(status=IssueStatus.SOLVED).count()
        ongoing = qs.filter(status=IssueStatus.ONGOING).count()

        avg_days = (
            qs.filter(resolve_date__isnull=False)
            .annotate(days=F("resolve_date") - F("date"))
            .aggregate(avg=Avg("days"))["avg"]
        )

        return Response({
            "total": total,
            "solved": solved,
            "ongoing": ongoing,
            "solve_rate": round(solved / total, 4) if total else 0,
            "avg_resolution_days": round(avg_days.days, 1) if avg_days else None,
        })


class ByCarrierView(APIView):
    """
    GET /api/v1/analytics/by-carrier/
    Instances and % per carrier — mirrors the pivot table in the Analysis sheet.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = _base_qs(request)
        total = qs.count() or 1

        rows = (
            qs.values(carrier_name=F("carrier__name"))
            .annotate(instances=Count("id"))
            .annotate(pct=Count("id") * 1.0 / total)
            .order_by("-instances")
        )

        return Response(list(rows))


class ByIssueTypeView(APIView):
    """
    GET /api/v1/analytics/by-issue-type/
    Breakdown by issue type code + description.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = _base_qs(request)
        total = qs.count() or 1

        rows = (
            qs.values(code=F("issue_type__code"), description=F("issue_type__description"))
            .annotate(instances=Count("id"))
            .annotate(pct=Count("id") * 1.0 / total)
            .order_by("-instances")
        )

        return Response(list(rows))


class ByCausingPartyView(APIView):
    """
    GET /api/v1/analytics/by-causing-party/
    Breakdown by causing party (SUPPLIER / CARRIER / MIXED).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = _base_qs(request)
        total = qs.count() or 1

        rows = (
            qs.values("causing_party")
            .annotate(instances=Count("id"))
            .annotate(pct=Count("id") * 1.0 / total)
            .order_by("-instances")
        )

        return Response(list(rows))


class ByMonthView(APIView):
    """
    GET /api/v1/analytics/by-month/
    Monthly trend — instances, solved, ongoing.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = _base_qs(request)

        rows = (
            qs.annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                instances=Count("id"),
                solved=Count("id", filter=Q(status=IssueStatus.SOLVED)),
                ongoing=Count("id", filter=Q(status=IssueStatus.ONGOING)),
            )
            .order_by("month")
        )

        return Response(list(rows))


class ByLocationView(APIView):
    """
    GET /api/v1/analytics/by-location/
    Breakdown per location code.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = _base_qs(request)
        total = qs.count() or 1

        rows = (
            qs.values(
                location_code=F("location__location_code"),
                city=F("location__city"),
            )
            .annotate(instances=Count("id"))
            .annotate(pct=Count("id") * 1.0 / total)
            .order_by("-instances")
        )

        return Response(list(rows))
