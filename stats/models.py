from django.db import models
from django.conf import settings
from media.models import MediaItem
from django.utils import timezone

class DownloadLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='downloads')
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_today(self):
        return self.created_at.date() == timezone.now().date()
    
    def __str__(self):
        return f"{self.user} downloaded {self.media_item} at {self.created_at}"

class ViewHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='view_history')
    media_item = models.ForeignKey(MediaItem, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        unique_together = ('user', 'media_item')
    
    def __str__(self):
        return f"{self.user} viewed {self.media_item}"
