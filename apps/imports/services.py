"""
Excel import logic, kept separate from the management command
so it can be called from tests or the API upload endpoint.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from apps.grief.models import Carrier, GriefIssue, IssueType, Location

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    locations_created: int = 0
    carriers_created: int = 0
    issue_types_created: int = 0
    issues_created: int = 0
    issues_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        return (
            f"Locations: +{self.locations_created} | "
            f"Carriers: +{self.carriers_created} | "
            f"Issue types: +{self.issue_types_created} | "
            f"Issues: +{self.issues_created} created, {self.issues_skipped} skipped | "
            f"Errors: {len(self.errors)}"
        )


def _safe_str(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


def _safe_date(val):
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def _safe_bool(val) -> bool:
    if pd.isna(val):
        return False
    return str(val).strip().lower() in ("yes", "true", "1")


# ── Sheet importers ───────────────────────────────────────────────────────────

def import_formulas_sheet(df: pd.DataFrame, result: ImportResult) -> None:
    """
    Formulas sheet (row 2 = headers at index 2).

    cols: Issue Type | description | Image | Causing Party | Status
          | month nr | month name | Carriers | RoadLOG Codes | Loc
    """
    # Header is at row index 2 (0-based)
    df.columns = df.iloc[2]
    data = df.iloc[3:].reset_index(drop=True)

    # --- Issue types (col 0 + 1) ---
    for _, row in data.iterrows():
        code = _safe_str(row.iloc[0])
        desc = _safe_str(row.iloc[1])
        if code:
            _, created = IssueType.objects.get_or_create(
                code=code,
                defaults={"description": desc},
            )
            if created:
                result.issue_types_created += 1

    # --- Carriers (col 7) ---
    carrier_col = data.iloc[:, 7] if data.shape[1] > 7 else pd.Series(dtype=str)
    for val in carrier_col:
        name = _safe_str(val)
        if name:
            _, created = Carrier.objects.get_or_create(name=name)
            if created:
                result.carriers_created += 1


def import_loc_codes_sheet(df: pd.DataFrame, result: ImportResult) -> None:
    """
    Loc Codes sheet — row 1 is the header (0-based index 1).
    Cols: Facility | NCC Entity Code | NCC Location code | Active indicator |
          Facility Name | Street+Number | Postal code | City | Country | Active |
          Truck | Delivery group | Delivery Location | Broker name | ...
    """
    df.columns = df.iloc[1]
    data = df.iloc[2:].reset_index(drop=True)

    for _, row in data.iterrows():
        loc_code = _safe_str(row.get("NCC Location code", ""))
        if not loc_code:
            continue

        active_raw = _safe_str(row.get("Active indicator", ""))
        active = active_raw.lower() in ("true", "yes", "y", "1")

        _, created = Location.objects.update_or_create(
            location_code=loc_code,
            defaults={
                "facility": _safe_str(row.get("Facility", "")),
                "entity_code": _safe_str(row.get("NCC Entity Code", "")),
                "facility_name": _safe_str(row.get("Facility Name", "")),
                "street": _safe_str(row.get("Street + Number", "")),
                "postal_code": _safe_str(row.get("Postal code", "")),
                "city": _safe_str(row.get("City", "")),
                "country": _safe_str(row.get("Country", "")),
                "active": active,
                "delivery_group": _safe_str(row.get("Delivery group", "")),
                "broker_name": _safe_str(row.get("Broker name", "")),
            },
        )
        if created:
            result.locations_created += 1


def _get_cached_carrier(
    name: str, cache: dict[str, Carrier | None],
) -> Carrier | None:
    """Get or create a carrier with caching."""
    if name not in cache:
        try:
            cache[name] = Carrier.objects.get(name__iexact=name) if name else None
        except Carrier.DoesNotExist:
            obj, _ = Carrier.objects.get_or_create(name=name)
            cache[name] = obj
    return cache[name]


def _get_cached_issue_type(
    code: str, cache: dict[str, IssueType | None],
) -> IssueType | None:
    """Get or create an issue type with caching."""
    if code not in cache:
        try:
            cache[code] = IssueType.objects.get(code__iexact=code) if code else None
        except IssueType.DoesNotExist:
            obj, _ = IssueType.objects.get_or_create(code=code)
            cache[code] = obj
    return cache[code]


def _get_cached_location(
    code: str, cache: dict[str, Location | None],
) -> Location | None:
    """Get or return None for a location with caching."""
    if code not in cache:
        try:
            cache[code] = Location.objects.get(location_code=code) if code else None
        except Location.DoesNotExist:
            cache[code] = None
    return cache[code]


def _process_grief_row(
    idx: int,
    row,
    result: ImportResult,
    carrier_cache: dict[str, Carrier | None],
    issue_type_cache: dict[str, IssueType | None],
    location_cache: dict[str, Location | None],
) -> None:
    """Process a single row from the grief sheet."""
    kn_ref = _safe_str(row.get("K&N REF", ""))
    if not kn_ref:
        return

    issue_code = _safe_str(row.get("Issue type", ""))
    unique_key = _safe_str(row.get("Unique", "")) or f"{kn_ref}{issue_code}"

    # Skip duplicates
    if GriefIssue.objects.filter(unique_key=unique_key).exists():
        result.issues_skipped += 1
        return

    try:
        issue_date = _safe_date(row.get("Date"))
        if not issue_date:
            result.errors.append(f"Row {idx}: missing date for {kn_ref}")
            return

        GriefIssue.objects.create(
            kn_ref=kn_ref,
            ship_id=_safe_str(row.get("Ship ID", "")),
            to_ref=_safe_str(row.get("TO Ref", "")),
            supplier_name=_safe_str(row.get("Supplier Name", "")),
            country=_safe_str(row.get("Ctry", "")),
            location=_get_cached_location(_safe_str(row.get("Loc", "")), location_cache),
            carrier=_get_cached_carrier(_safe_str(row.get("Carrier", "")), carrier_cache),
            issue_type=_get_cached_issue_type(issue_code, issue_type_cache),
            date=issue_date,
            has_image=_safe_bool(row.get("Image")),
            causing_party=_safe_str(row.get("Causing party", "")).upper(),
            resolve_date=_safe_date(row.get("Resolve Date")),
            status=_safe_str(row.get("Status", "ONGOING")).upper(),
            note=_safe_str(row.get("Note", "")),
            unique_key=unique_key,
        )
        result.issues_created += 1

    except Exception as exc:
        msg = f"Row {idx} ({kn_ref}): {exc}"
        logger.warning(msg)
        result.errors.append(msg)


def import_grief_sheet(df: pd.DataFrame, result: ImportResult) -> None:
    """
    Grief sheet — header at row index 9.

    Cols: K&N REF | Ship ID | TO Ref | Supplier Name | Ctry | Loc | Carrier |
          Issue type | Date | Image | Causing party | Resolve Date | Status | Note |
          Unique | Year | Month | Duplicate | Solved | Ongoing
    """
    df.columns = df.iloc[9]
    data = df.iloc[10:].reset_index(drop=True)

    # Build lookup caches to avoid per-row DB hits
    carrier_cache: dict[str, Carrier | None] = {}
    issue_type_cache: dict[str, IssueType | None] = {}
    location_cache: dict[str, Location | None] = {}

    for idx, row in data.iterrows():
        _process_grief_row(
            idx,
            row,
            result,
            carrier_cache,
            issue_type_cache,
            location_cache,
        )


# ── Public entrypoint ─────────────────────────────────────────────────────────

def import_excel_file(path: str | Path) -> ImportResult:
    """
    Import all reference data and grief issues from an Excel/xlsm file.
    Safe to run multiple times — existing records are skipped or updated.
    """
    result = ImportResult()
    logger.info("Starting import from %s", path)

    all_sheets: dict[str, pd.DataFrame] = pd.read_excel(
        path, sheet_name=None, header=None, dtype=str,
    )

    # Order matters: reference data first, then issues
    if "Formulas" in all_sheets:
        import_formulas_sheet(all_sheets["Formulas"].copy(), result)
        logger.info(
            "Formulas sheet done: %s issue types, %s carriers",
            result.issue_types_created,
            result.carriers_created,
        )

    if "Loc Codes" in all_sheets:
        import_loc_codes_sheet(all_sheets["Loc Codes"].copy(), result)
        logger.info("Loc Codes sheet done: %s locations", result.locations_created)

    if "Grief" in all_sheets:
        import_grief_sheet(all_sheets["Grief"].copy(), result)
        logger.info(
            "Grief sheet done: %s created, %s skipped",
            result.issues_created,
            result.issues_skipped,
        )

    logger.info("Import complete — %s", result.summary())
    return result
