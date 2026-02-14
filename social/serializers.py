from rest_framework import serializers
from .models import Like, Review, Follow
from core.serializers import UserSerializer

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Like
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'user_details', 'media_item', 'rating', 'content', 'created_at']
        read_only_fields = ['user', 'created_at']

class FollowSerializer(serializers.ModelSerializer):
    follower_details = UserSerializer(source='follower', read_only=True)
    followed_details = UserSerializer(source='followed', read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'follower_details', 'followed_details', 'created_at']
        read_only_fields = ['follower', 'created_at', 'follower_details', 'followed_details']
