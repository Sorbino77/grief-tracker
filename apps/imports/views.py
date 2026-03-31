import tempfile
from pathlib import Path

from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import import_excel_file


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

        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in (".xlsx", ".xlsm", ".xls"):
            return Response(
                {"detail": "Unsupported file type. Use .xlsx or .xlsm."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        try:
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
