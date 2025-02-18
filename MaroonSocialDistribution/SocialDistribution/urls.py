from django.urls import path
from . import views

app_name = 'SocialDistribution'

urlpatterns = [
    path("", views.index, name="index"),
    # Create profile interface page
    path("create-profile", views.create_profile, name="create-profile"),
    # API endpoint for adding profile
    path("add-profile", views.add_profile, name = "add-profile"),
    # View profile page
    path("authors/<uuid:uuid>", views.view_profile, name = "view-profile"),
    # API endpoint for "Authors API"
    path("api/authors", views.authors_list, name="authors-list"),
    #TODO API endpoint for "Single Author API"
    path("<uuid:uuid>/edit-profile", views.edit_profile, name = "edit-profile"),
    path("<uuid:uuid>/update-profile", views.update_profile, name = "update-profile"),
    
    # Viewing all of an author's posts
    path("authors/<uuid:uuid>/posts", views.author_posts, name = "author-posts"),
    # Create post interface page
    path("<uuid:uuid>/create-post", views.create_post, name = "create-post"),
    # API endpoint for adding post
    path("<uuid:uuid>/add-post", views.add_post, name = "add-post"),
]