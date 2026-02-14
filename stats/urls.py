from django.urls import path
from .views import DownloadMediaView

urlpatterns = [
    path('download/<int:pk>/', DownloadMediaView.as_view(), name='download-media'),
]
