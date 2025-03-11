from django.urls import path
from django.contrib import admin
from . import views
from django.contrib.auth.views import LogoutView
from .views_stream import stream_view  # import stream_view (reading)
from .views import (
    search_authors, send_follow_request, accept_follow_request, reject_follow_request, follow_requests,
    view_followers, view_following, view_friends, unfollow_user, remove_follower, delete_post, edit_post, check_follow_status, followers_list, following_list, friends_list, view_unlisted_post
)

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView



app_name = 'SocialDistribution'

urlpatterns = [
    
    path("", views.index, name="index"),

    ### API DOCUMENTATION  ###
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-docs"),
    path("api/docs/custom/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-documentation"),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc-docs'),


    ### ADMIN / MISC ###
    # Admin / Misc API Endpoints
    path("admin/", admin.site.urls),    # Django's built in admin panel
    path('admin/add-author/', views.add_author, name='add-author'), #add author
    path('admin/edit-author/<uuid:uuid>/', views.edit_author_profile, name='edit-author-profile'), #edit author
    path('admin/delete-author/<uuid:uuid>/', views.delete_author, name='delete-author'), #delete author
    # Admin / Misc - Page Rendering
    path("login", views.author_login, name = "author-login"),
    path('logout/', views.author_logout, name='author-logout'),
    path("authors/search/", views.search_authors, name="search-authors"),


    #### AUTHORS ###
    # Authors - API Endpoints 
    path("api/authors", views.authors_list, name="authors-list"), # Authors API
    path("api/authors/<uuid:uuid>", views.author_profile, name = "author-profile"), # Single Author API {AUTHOR_SERIAL}
    path("api/authors/<str:fqid>", views.author_profile_fqid, name = "author-profile-fqid"), # Single Author API {AUTHOR_FQID}
    path("add-profile", views.add_profile, name = "add-profile"), # API endpoint for adding profile
    # Authors - Page rendering
    path("create-profile", views.create_profile, name="create-profile"), # Create profile interface page
    path("<uuid:uuid>/edit-profile", views.edit_profile, name = "edit-profile"), # Edit profile page
    path("authors/<uuid:uuid>", views.view_profile, name = "view-profile"), # View profile page


    ### POSTS ###
    # Posts - API endpoints
    path("<uuid:uuid>/add-post", views.add_post, name = "add-post"),
    path("authors/<uuid:author_uuid>/posts/<int:post_id>/delete/", delete_post, name="delete_post"),
    path("authors/<uuid:author_uuid>/posts/<int:post_id>/edit/", edit_post, name="edit_post"),
    # Posts - Page Rendering
    path("authors/<uuid:uuid>/posts", views.author_posts, name = "author-posts"), # Viewing all of an author's posts
    path("<uuid:uuid>/create-post", views.create_post, name = "create-post"), # Create post interface page


    ### FOLLOWING ###
    # TODO Sort this into two categories
    # 1. Following - API Endpoints
    # 2. Following - Page Rendering
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


    ### READING ### 
    # TODO tidy this up
    ######################## reading starts here ###########################
    path('stream/', stream_view, name='stream'),
    
    ##################### reading ends ############################

    # unlisted
    path("posts/<int:post_id>/unlisted", view_unlisted_post, name="view-unlisted-post"),
    path("posts/<int:post_id>/", views.view_single_post, name="view-single-post"),


    path("posts/<int:post_id>/send-to-followers/", views.send_post_to_followers, name="send-to-followers"),
    path("inbox/", views.view_inbox, name="view-inbox"),


    ### LIKES ###

    # Likes - API Endpoints
    # TODO change to post_uuid if/when uuid is available for posts?
    path('api/authors/<uuid:author_uuid>/posts/<int:post_id>/likes', views.get_post_likes, name='post_likes'), # Get likes of a single post
    path('api/authors/<uuid:author_uuid>/liked', views.get_likes_by_author, name='get_likes_by_author'), # Get liked objects by author
    path('api/authors/<uuid:author_uuid>/liked/<uuid:like_uuid>', views.get_single_like, name='get_single_like'), # Get a single like
    # TODO add fqid related apis

    # Like creation
    # TODO change to handle uuid of post?
    path('post/<int:post_id>/like_post/', views.like_post, name="like-post"),
    path('comment/<uuid:comment_uuid>/like_comment/', views.like_comment, name="like-comment"),

    ### COMMENTS ###
    # Comment creation
    path('post/<int:post_id>/add_comment/', views.add_comment, name="add-comment"),

    # API Endpoints
    path('api/authors/<uuid:author_uuid>/posts/<int:post_id>/comments', views.get_post_comments, name='post_comments'), # Get comments of a single post
    path('api/authors/<uuid:author_uuid>/commented', views.get_comments_by_author, name='get_comments_by_author'), # Get comments by author
    path('api/authors/<uuid:author_uuid>/commented/<uuid:comment_uuid>', views.get_single_comment, name='get_single_comment'), # Get a single comment

]