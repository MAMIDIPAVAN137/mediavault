from django.contrib import admin
from .models import Like, Follow, MediaView, Favorite, Review

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'created_at')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'followed', 'created_at')

@admin.register(MediaView)
class MediaViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'created_at')
    list_filter = ('created_at',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'created_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('content',)
