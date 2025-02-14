from django.db import models
import uuid

# Create your models here.
class Author(models.Model):
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