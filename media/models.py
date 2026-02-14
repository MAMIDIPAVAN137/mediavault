from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os
import uuid

def media_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('uploads', str(instance.uploader.id), filename)

def thumbnail_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('thumbnails', str(instance.uploader.id), filename)

class Folder(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='folders')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subfolders', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cover_image = models.ImageField(upload_to='folder_covers/', null=True, blank=True)
    is_private = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'parent', 'owner')

    def __str__(self):
        return self.name
    
    @property
    def effective_cover(self):
        if self.cover_image:
            return self.cover_image.url
        # Default: first image in folder
        first_img = self.media_items.filter(media_type='IMAGE').first()
        if first_img:
            return first_img.file.url
        return None
    
    def get_ancestors(self):
        ancestors = []
        current = self
        while current.parent:
            current = current.parent
            ancestors.append(current)
        return ancestors[::-1]

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class MediaItem(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('VIDEO', 'Video'),
        ('IMAGE', 'Image'),
        ('DOCUMENT', 'Document'),
        ('OTHER', 'Other'),
    )

    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='media_items')
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, related_name='media_items', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='media_items', null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=media_file_path)
    thumbnail = models.ImageField(upload_to=thumbnail_path, null=True, blank=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES)
    duration = models.FloatField(null=True, blank=True) # Duration in seconds
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    downloads_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_processed = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or str(self.file.name)

    def save(self, *args, **kwargs):
        if not self.file:
            super().save(*args, **kwargs)
            return

        if not self.title:
            self.title = os.path.basename(self.file.name)
        
        # Determine media type from extension automatically
        try:
            filename = self.file.name
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']:
                self.media_type = 'IMAGE'
            elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv']:
                self.media_type = 'VIDEO'
            elif ext in ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z', '.xls', '.xlsx', '.ppt', '.pptx', '.csv']:
                self.media_type = 'DOCUMENT'
            else:
                self.media_type = 'OTHER'
        except Exception:
            self.media_type = 'OTHER'
        
        super().save(*args, **kwargs)

class Collection(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collections')
    items = models.ManyToManyField(MediaItem, related_name='collections', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
