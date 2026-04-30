import logging
import tempfile
from pathlib import Path

from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import import_excel_file

logger = logging.getLogger(__name__)
audit = logging.getLogger("audit")

# 10 MB upload cap. DATA_UPLOAD_MAX_MEMORY_SIZE in settings/base.py also caps
# this at the request-body level, but we double-check here so a clear error
# message comes back rather than Django\'s generic 413.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = (".xlsx", ".xlsm", ".xls")


class ExcelUploadView(APIView):
    """
    POST /api/v1/imports/upload/
    Upload an Excel file to import grief data. Admin only.

    Form field: file  (multipart/form-data)
    """
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAdminUser]

    def post(self, request: Request) -> Response:
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # ── Size guard ──
        if uploaded.size and uploaded.size > MAX_UPLOAD_BYTES:
            return Response(
                {"detail": f"File too large. Max {MAX_UPLOAD_BYTES // 1024 // 1024} MB."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # ── Suffix guard ──
        # Use Path(...).name first so we never trust a path-traversal-laden
        # uploaded.name like "../../etc/passwd.xlsx".
        original_name = Path(uploaded.name).name
        suffix = Path(original_name).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            return Response(
                {"detail": f"Unsupported file type. Use one of: {', '.join(ALLOWED_SUFFIXES)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Stream to a temp file with the safe suffix only (not the user-controlled
        #    name) so nothing on disk reflects untrusted input.
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        try:
            audit.info(
                "excel_upload user=%s original_name=%s size=%s",
                getattr(request.user, "pk", None), original_name, uploaded.size,
            )
            result = import_excel_file(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        return Response(
            {
                "summary": result.summary(),
                "locations_created": result.locations_created,
                "carriers_created": result.carriers_created,
                "issue_types_created": result.issue_types_created,
                "issues_created": result.issues_created,
                "issues_skipped": result.issues_skipped,
                "errors": result.errors[:50],  # cap to avoid huge responses
            },
            status=status.HTTP_200_OK,
        )
