from django.urls import path
from .views import ExcelDataExtractionView

urlpatterns = [
    # path('format1/', ExtractDataAPIView.as_view(), name='format-excel1'),
    path('format/', ExcelDataExtractionView.as_view(), name='format-excel'),
]
