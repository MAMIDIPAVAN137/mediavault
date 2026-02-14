from rest_framework import serializers
from .models import Folder, MediaItem, Collection, Category
from core.serializers import UserSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class FolderSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    class Meta:
        model = Folder
        fields = '__all__'
        read_only_fields = ['owner', 'created_at', 'updated_at']

class MediaItemSerializer(serializers.ModelSerializer):
    uploader = UserSerializer(read_only=True)
    extension = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = MediaItem
        fields = '__all__'
        read_only_fields = ['uploader', 'created_at', 'updated_at', 'views_count', 'downloads_count', 'media_type', 'duration', 'width', 'height', 'is_processed']

    def get_extension(self, obj):
        return obj.file.name.split('.')[-1] if obj.file else ''

class CollectionSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    items = MediaItemSerializer(many=True, read_only=True)
    class Meta:
        model = Collection
        fields = '__all__'
        read_only_fields = ['owner', 'created_at']
