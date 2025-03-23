from rest_framework import serializers
from .models import Author, Post, FollowRequest, Like, Comment
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    id = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False)  # Ensure image is optional
    likes = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['type', 'title', 'id', 'page', 'description', 'contentType', 'content', 'author', 'comments', 'likes', 'published', 'visibility', 'image']

    def get_id(self, obj):
        return obj.id
    
    def get_comments(self, obj):
        comments = Comment.objects.filter(post=obj)
        return CommentSerializer(comments, many=True).data
    
    def get_likes(self, obj):
        likes = Like.objects.filter(post=obj)
        return LikeSerializer(likes, many=True).data
    
class FollowRequestSerializer(serializers.ModelSerializer):
    sender = AuthorSerializer(read_only=True)
    receiver = AuthorSerializer(read_only=True)
    accepted = serializers.BooleanField(default=False)

    class Meta:
        model = FollowRequest
        fields = ["id", "sender", "receiver", "accepted"]


class LikeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="like")
    author = AuthorSerializer()
    published = serializers.DateTimeField(default=timezone.now)
    object = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = ['type', 'author', 'published', 'id', 'object']

    def get_object(self, instance):
        # If the object field is already populated, use it directly
        if instance.object:
            return instance.object
        
        # If the object field is not populated decide if it's a post or comment and use its ID for the URL
        # TODO change post.id to post.uuid if we update post model to have uuid field
        node_url = "http://maroonnode.com"
        if instance.post:
            return f"{node_url}/api/authors/{instance.author.uuid}/posts/{instance.post.id}"
        elif instance.comment:
            return f"{node_url}/api/authors/{instance.author.uuid}/comments/{instance.comment.uuid}"
        return None

class CommentSerializer(serializers.ModelSerializer):
    # url id field
    # Fields that will be modified for the API response
    id = serializers.SerializerMethodField()
    author = AuthorSerializer()
    likes = LikeSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        fields = ['type','author', 'comment', 'contentType', 'published', 'id', 'post', 'likes']
    
    def get_id(self, obj):
        return obj.id