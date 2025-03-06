from django.urls import path
from django.contrib import admin
from . import views
from django.contrib.auth.views import LogoutView
from .views_stream import stream_view  # import stream_view (reading)
from .views import (
    search_authors, send_follow_request, accept_follow_request, reject_follow_request, follow_requests,
    view_followers, view_following, view_friends, unfollow_user, remove_follower, delete_post, edit_post, check_follow_status, followers_list, following_list, friends_list, view_unlisted_post
)

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


app_name = 'SocialDistribution'

urlpatterns = [
    
    path("", views.index, name="index"),

    # API Endpoint documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-docs"),

    #API Endpoints
    ################
    # API endpoint for "Authors API"
    path("api/authors", views.authors_list, name="authors-list"),
    #TODO API endpoint for "Single Author API"


    # PROFILE
    # Create profile interface page
    path("create-profile", views.create_profile, name="create-profile"),
    # API endpoint for adding profile
    path("add-profile", views.add_profile, name = "add-profile"),
    # View profile page
    path("authors/<uuid:uuid>", views.view_profile, name = "view-profile"),
    path("<uuid:uuid>/edit-profile", views.edit_profile, name = "edit-profile"),
    path("<uuid:uuid>/update-profile", views.update_profile, name = "update-profile"),
    path("login", views.author_login, name = "author-login"),
    
    # Viewing all of an author's posts
    path("authors/<uuid:uuid>/posts", views.author_posts, name = "author-posts"),
    # Create post interface page
    path("<uuid:uuid>/create-post", views.create_post, name = "create-post"),
    # API endpoint for adding post
    path("<uuid:uuid>/add-post", views.add_post, name = "add-post"),

    # Delete post
    path("authors/<uuid:author_uuid>/posts/<int:post_id>/delete/", delete_post, name="delete_post"),

    path("authors/<uuid:author_uuid>/posts/<int:post_id>/edit/", edit_post, name="edit_post"),


    path("authors/search/", views.search_authors, name="search-authors"),
    path("authors/<uuid:uuid>/follow/", send_follow_request, name="send-follow-request"),
    path("authors/<uuid:sender_uuid>/accept-follow/", accept_follow_request, name="accept-follow-request"),
    path("authors/<uuid:sender_uuid>/reject-follow/", reject_follow_request, name="reject-follow-request"),
    path("authors/follow-requests/", follow_requests, name="follow-requests"),
    path("authors/followers/", view_followers, name="view-followers"),  
    path("authors/following/", view_following, name="view-following"), 
    path("authors/friends/", view_friends, name="view-friends"),
    path("authors/<uuid:uuid>/unfollow/", unfollow_user, name="unfollow-user"),
    path("authors/<uuid:uuid>/remove-follower/", remove_follower, name="remove-follower"),
    path("authors/<uuid:uuid>/follow-status/<uuid:foreign_author_uuid>/", check_follow_status, name="check-follow-status"),

    path("authors/<uuid:uuid>/followers/", followers_list, name="followers-list"),
    path("authors/<uuid:uuid>/following/", following_list, name="following-list"),
    path("authors/<uuid:uuid>/friends/", friends_list, name="friends-list"),


    
    ######################## reading starts here ###########################
    path('stream/', stream_view, name='stream'),
    
    # logout
    path('logout/', views.author_logout, name='author-logout'),
    ##################### reading ends ############################

    # unlisted
    path("posts/<int:post_id>/unlisted", view_unlisted_post, name="view-unlisted-post"),

    path("admin/", admin.site.urls),    # Django's built in admin panel

]