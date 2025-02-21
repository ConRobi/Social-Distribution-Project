from django.db import models
import uuid
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Author(AbstractUser):
    # Model based on object:
    # https://uofa-cmput404.github.io/general/project.html#single-author-api:~:text=API%20Objects-,Example%20Author%20Objects,-%7B%0A%20%20%20%20//%20Author%20object
    
    type = models.CharField(max_length=10, default='author')
    id = models.URLField()
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True) # TODO enforce uniqueness across nodes
    host = models.URLField()
    display_name = models.CharField(max_length=255)
    github = models.URLField(blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True)
    page = models.URLField(blank=True, null=True)
    last_checked = models.DateTimeField(default=now)

"""
type, title, id, page, description, content_type, content, author: {have author object in here}, comments: {comment object},
likes: {like object}, published, visibility
"""
class Post(models.Model):
    # type = models.CharField(max_length=10, default='post')
    title = models.CharField(max_length=255)
    # id = models.URLField(primary_key=True)
    # page = models.URLField(blank=True, null=True)
    description = models.TextField()
    """
    assume either
    text/markdown -- common mark
    text/plain -- UTF-8
    application/base64 # this an image that is neither a jpeg or png
    image/png;base64 # this is an png -- images are POSTS. So you might have a user make 2 posts if a post includes an image!
    image/jpeg;base64 # this is an jpeg
    for HTML you will want to strip tags before displaying
    """
    # content_type = models.CharField(max_length=20)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    # Need a comment object first?
    # comments = models.ManyToManyField('Comment', blank=True)
    # Need a like object first?
    # likes = models.ManyToManyField('Like', blank=True)
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(max_length=10, choices=[
        ('PUBLIC', 'Public'),
        ('FRIENDS', 'Friends Only'),
        ('DELETED', 'Deleted'),
    ],
    default='PUBLIC')