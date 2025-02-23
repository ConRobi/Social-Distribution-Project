from rest_framework import serializers
from .models import Author, Post, FollowRequest
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

class AuthorSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="author")
    id = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    page = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ["type", "id", "host", "display_name", "github", "profile_image", "page"]

    def get_id(self, obj):
        return obj.id

    def get_host(self, obj):
        return obj.host

    def get_page(self, obj):
        return obj.page

    
class PostSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)  # Ensure image is optional

    class Meta:
        model = Post
        fields = '__all__'
    
    # Create and return a new post instance with the validated data
    def create(self, validated_data):
        return super().create(validated_data)

class FollowRequestSerializer(serializers.ModelSerializer):
    sender = AuthorSerializer(read_only=True)
    receiver = AuthorSerializer(read_only=True)
    accepted = serializers.BooleanField(default=False)

    class Meta:
        model = FollowRequest
        fields = ["id", "sender", "receiver", "accepted"]