from django.db import models

# Create your models here.
class Author(models.Model):
    
    type = models.CharField(max_length=10, default='author')
    id = models.URLField(primary_key=True)  # Using URLField since the ID is a URL
    host = models.URLField()
    display_name = models.CharField(max_length=255)
    github = models.URLField(blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True)
    page = models.URLField(blank=True, null=True)
