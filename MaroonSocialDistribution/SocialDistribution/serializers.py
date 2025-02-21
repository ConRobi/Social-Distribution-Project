from rest_framework import serializers
from .models import Author, Post
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
    class Meta:
        model = Post
        fields = ["title", "description", "content", "visibility", "author"]
    
    def create(self, validated_data):
        return super().create(validated_data)
        

# class PostSerializer(serializers.ModelSerializer):
#     type = serializers.CharField(default="post")
#     id = serializers.SerializerMethodField(read_only=True)
#     page = serializers.SerializerMethodField(read_only=True)
#     author = AuthorSerializer()

#     class Meta:
#         model = Post
#         fields = ["title", "description", "content", "visibility"]
#         # fields = ["type", "id", "title", "page", "description", "content_type", "content", "author", "published", "visibility"]

#     def create(self, validated_data):
#         print(validated_data)
#         return super().create(validated_data)
    
#     def get_id(self, obj):
#         return obj.id

#     def get_page(self, obj):
#         return obj.page