from django.db import models
import uuid
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser
import commonmark
from django.contrib.auth.models import User  # Import User model if necessary
from django.conf import settings  # Import settings to get the custom user model

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


    def get_followers(self):
        """Returns a list of authors who follow this author"""
        return Author.objects.filter(
            uuid__in=FollowRequest.objects.filter(receiver=self, status='ACCEPTED').values_list('sender__uuid', flat=True)
        )

    def get_following(self):
        """Returns a list of authors this author follows"""
        return Author.objects.filter(
            uuid__in=FollowRequest.objects.filter(sender=self, status='ACCEPTED').values_list('receiver__uuid', flat=True)
        )

    def get_friends(self):
        """Returns a list of mutual followers (friends)"""
        followers = self.get_followers().values_list("uuid", flat=True)
        return self.get_following().filter(uuid__in=followers)

"""
type, title, id, page, description, content_type, content, author: {have author object in here}, comments: {comment object},
likes: {like object}, published, visibility
"""
class Post(models.Model):
    type = models.CharField(max_length=10, default='post')
    title = models.CharField(max_length=255)
    # id = models.URLField(primary_key=True)
    # page = models.URLField(blank=True, null=True)
    description = models.TextField()
    contentType = models.CharField(max_length=20, choices=[
        ('text/markdown', 'CommonMark'),
        ('text/plain', 'plaintext'),
        ('image/png;base64', 'pngImage'),
        ('image/jpeg;base64', 'jpegImage'),
        ('application/base64', 'otherImage')
    ])
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
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)  # Ensure correct field

    """
    If CommonMark is selected then format it, else leave the content as it is
    """
    def render_content(self):
        if self.contentType == 'text/markdown':
            return commonmark.commonmark(self.content)
        elif self.contentType == 'text/plain':
            return f"<pre>{self.content}</pre>"
        # If the contentType is for an image
        else:
            return self.content

class FollowRequest(models.Model):
    """
    Model for handling follow requests between authors.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    sender = models.ForeignKey(Author, related_name="follow_requests_sent", on_delete=models.CASCADE)
    receiver = models.ForeignKey(Author, related_name="follow_requests_received", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.display_name} -> {self.receiver.display_name} ({self.status})"



class InboxPost(models.Model):
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    received_at = models.DateTimeField(auto_now_add=True)
