from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    folder_detail, set_folder_cover, delete_media, delete_folder, 
    edit_folder, edit_media, media_detail, toggle_media_visibility, toggle_folder_visibility,
    bulk_delete, all_media
)
from .api_views import MediaItemViewSet

router = DefaultRouter()
router.register(r'items', MediaItemViewSet, basename='mediaitem')

urlpatterns = [
    path('', include(router.urls)),
    path('folder/<int:pk>/', folder_detail, name='folder_detail'),
    path('folder/<int:folder_pk>/set-cover/<int:media_pk>/', set_folder_cover, name='set-folder-cover'),
    path('folder/edit/<int:pk>/', edit_folder, name='folder-edit'),
    path('folder/delete/<int:pk>/', delete_folder, name='folder-delete'),
    path('bulk-delete/', bulk_delete, name='bulk-delete'),
    
    path('edit/<int:pk>/', edit_media, name='media-edit'),
    path('view/<int:pk>/', media_detail, name='media-detail-page'),
    path('delete/<int:pk>/', delete_media, name='media-delete'),
    
    path('all/', all_media, name='all-media'),
    path('visibility/media/<int:pk>/<str:action>/', toggle_media_visibility, name='media-visibility'),
    path('visibility/folder/<int:pk>/<str:action>/', toggle_folder_visibility, name='folder-visibility'),
]
