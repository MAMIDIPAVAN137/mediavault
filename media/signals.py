import os
import subprocess
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MediaItem
from django.core.files import File

@receiver(post_save, sender=MediaItem)
def generate_thumbnail(sender, instance, created, **kwargs):
    if created and instance.media_type == 'VIDEO' and not instance.thumbnail:
        try:
            # Assume file is available locally (FileSystemStorage)
            if not instance.file:
                return

            video_path = instance.file.path
            base_dir = os.path.dirname(video_path)
            thumb_name = f"{instance.id}_thumb.jpg"
            thumb_path = os.path.join(base_dir, thumb_name)

            # Generate thumbnail
            subprocess.run([
                'ffmpeg', '-y', '-i', video_path, 
                '-ss', '00:00:01.000', '-vframes', '1', 
                thumb_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Save to instance
            if os.path.exists(thumb_path):
                with open(thumb_path, 'rb') as f:
                    instance.thumbnail.save(thumb_name, File(f), save=False)
                    instance.save(update_fields=['thumbnail'])
                
                # clean up temporary file
                os.remove(thumb_path)
                
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
