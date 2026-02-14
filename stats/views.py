from rest_framework import views, status, permissions
from rest_framework.response import Response
from .models import DownloadLog
from media.models import MediaItem
from django.utils import timezone
from django.shortcuts import get_object_or_404

class DownloadMediaView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        media_item = get_object_or_404(MediaItem, pk=pk)
        user = request.user
        
        if user.is_superuser or media_item.uploader == user:
            return Response({'status': 'allowed', 'url': media_item.file.url})

        # Check Uploader's download preferences
        uploader = media_item.uploader
        pref = uploader.download_preference

        if uploader.download_preference == 'RESTRICTED':
            # Check if user is an uploader/admin OR explicitly allowed
            is_explicitly_allowed = uploader.allowed_downloaders.filter(id=user.id).exists()
            if not (user.is_uploader or user.is_superuser or is_explicitly_allowed):
                return Response({'error': 'Downloads for this content are restricted. You need explicit permission from the uploader.'}, status=status.HTTP_403_FORBIDDEN)
        
        elif uploader.download_preference == 'FOLLOWERS':
            from social.models import Follow
            is_following = Follow.objects.filter(follower=user, followed=uploader, is_accepted=True).exists()
            if not is_following:
                return Response({'error': 'You must be a follower to download this user\'s content.'}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        # Filter accurately
        daily_downloads = DownloadLog.objects.filter(user=user, created_at__date=today)
        
        if media_item.media_type == 'VIDEO':
            video_downloads = daily_downloads.filter(media_item__media_type='VIDEO').count()
            if video_downloads >= 3:
                return Response({'error': 'Daily video download limit reached (3/3).'}, status=status.HTTP_403_FORBIDDEN)
        elif media_item.media_type == 'IMAGE':
            image_downloads = daily_downloads.filter(media_item__media_type='IMAGE').count()
            if image_downloads >= 5:
                return Response({'error': 'Daily image download limit reached (5/5).'}, status=status.HTTP_403_FORBIDDEN)
        
        DownloadLog.objects.create(user=user, media_item=media_item)
        media_item.downloads_count += 1
        media_item.save(update_fields=['downloads_count'])
        
        return Response({'status': 'allowed', 'url': media_item.file.url})
