from django.urls import path

from .views import ExcelUploadView

urlpatterns = [
    path("upload/", ExcelUploadView.as_view(), name="excel-upload"),
]
