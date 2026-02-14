from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import MediaItem, Folder
from .serializers import MediaItemSerializer
from django.shortcuts import get_object_or_404

class MediaItemViewSet(viewsets.ModelViewSet):
    serializer_class = MediaItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MediaItem.objects.filter(uploader=self.request.user)

    def perform_create(self, serializer):
        # Determine folder if relative_path is provided
        relative_path = self.request.data.get('relative_path')
        parent_folder_id = self.request.data.get('parent_folder_id')
        folder = None

        if parent_folder_id:
            folder = get_object_or_404(Folder, id=parent_folder_id, owner=self.request.user)
        
        if relative_path and '/' in relative_path:
            # Simple logic to handle folder structure from path
            path_parts = relative_path.split('/')[:-1] # Exclude filename
            current_parent = folder
            for part in path_parts:
                if part:
                    current_parent, created = Folder.objects.get_or_create(
                        name=part, owner=self.request.user, parent=current_parent
                    )
            folder = current_parent

        serializer.save(uploader=self.request.user, folder=folder)
