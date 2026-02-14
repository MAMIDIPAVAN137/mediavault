from rest_framework import permissions

class IsUploaderOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_uploader or request.user.is_superuser)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Handle cases where owner is 'uploader' field in MediaItem or 'owner' in Folder
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'uploader'):
            return obj.uploader == request.user
        return False
