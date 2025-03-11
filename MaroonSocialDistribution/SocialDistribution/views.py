from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Author, Post, FollowRequest, Like, Comment, InboxPost, AdminApproval
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, authenticate, logout
from .forms import AuthorRegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q
from .services.github_service import fetch_github_activity
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiTypes
from .serializers import AuthorSerializer, PostSerializer, FollowRequestSerializer, LikeSerializer, CommentSerializer
import urllib
import requests

def index(request):
    return render(request, "index.html")

### Likes ###

@api_view(['POST'])
@login_required
def like_post(request, post_id):
    '''
    - Description: Like a post
    - Returns: a Json Response with the post's like count (integer)
    '''
    # TODO Maybe change id to uuid if post object is updated with new primary key?
    post = get_object_or_404(Post, id=post_id)
    
    like_author = request.user
    like = Like.objects.filter(author=like_author, post=post)
    # Check if the user already liked this post
    if not like.exists():
        # Create new like object associated with the post
        new_like = Like.objects.create(author=like_author, post=post)
        new_like.id = f"{like_author.id}/liked/{new_like.uuid}"
        # TODO uncomment line when post model has proper id field
        # new_like.object = post.id
        new_like.save()
    else:
        # Remove like if already liked
        like.delete()
    
    # Return the new like count as a JSON response for use in Javascript
    return JsonResponse({'likes_count': post.likes.count()})

@api_view(['POST'])
@login_required
def like_comment(request, comment_uuid):
    '''
    - Description: Like a comment
    - Returns: a Json Response with the comment's like count (integer)
    '''
    comment = get_object_or_404(Comment, uuid=comment_uuid)

    like_author = request.user
    like = Like.objects.filter(author=like_author, comment=comment)
    # Check if the user already liked this comment
    if not like.exists():
        # Create new like object associated with the comment
        new_like = Like.objects.create(author=like_author, comment=comment)
        new_like.id = f"{like_author.id}/liked/{new_like.uuid}"
        # TODO uncomment line when comment model has proper id field
        # new_like.object = comment.id
        new_like.save()
    else:
        # Remove like if already liked
        like.delete()
    
    # Return the new like count as a JSON response for use in Javascript
    return JsonResponse({'likes_count': comment.likes.count()})


@extend_schema(
    description=("Get a list of likes for a specified post by a particular author.\n"
        "This endpoint is useful to retrieve all likes for a post, with pagination support.\n"
        "- **When to use**: When you need to retrieve the list of likes for a post, optionally using pagination.\n"
        "- **How to use**: Make a GET request to `api/authors/{author_uuid}/posts/{post_id}/likes`.\n"
        "- **Why to use**: Useful for clients that need to fetch the list of likes for posts, especially when dealing with large amounts of data and needing pagination.\n"
        "- **Why not use**: Do not use this endpoint if you don’t need the list of likes or when pagination is unnecessary."),
    responses={
        200: {
            "type": "object",
            "properties": {
                "type": {"type": "string", "example": "likes"},
                "page": {"type": "string", "example": "http://maroonnode.com/authors/222/posts/249"},
                "id": {"type": "string", "example": "http://maroonnode.com/api/authors/222/posts/249/likes"},
                "page_number": {"type": "integer", "example": 1},
                "size": {"type": "integer", "example": 50},
                "count": {"type": "integer", "example": 9001},
                "src": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "example": "like"},
                            "author": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "example": "author"},
                                    "id": {"type": "string", "example": "http://maroonnode.com/api/authors/111"},
                                    "page": {"type": "string", "example": "http://maroonnode.com/authors/greg"},
                                    "host": {"type": "string", "example": "http://maroonnode.com/api/"},
                                    "displayName": {"type": "string", "example": "Greg Johnson"},
                                    "github": {"type": "string", "example": "http://github.com/gjohnson"},
                                    "profileImage": {"type": "string", "example": "https://i.imgur.com/k7XVwpB.jpeg"}
                                }
                            },
                            "published": {"type": "string", "example": "2015-03-09T13:07:04+00:00"},
                            "id": {"type": "string", "example": "http://maroonnode.com/api/authors/111/liked/166"},
                            "object": {"type": "string", "example": "http://maroonnode.com/authors/222/posts/249"}
                        }
                    }
                }
            }
        }
    },
    parameters=[
        OpenApiParameter('size', OpenApiTypes.INT, description='Number of likes per page', required=False),
    ],
)
@api_view(['GET'])
def get_post_likes(request, author_uuid, post_id):
    post = get_object_or_404(Post, id=post_id, author__uuid=author_uuid)
    
    # Create a paginator object
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'size'  # Allows user to set ?size=
    paginator.page_size = request.GET.get('size', 5)  # Default size: 5
    paginator.max_page_size = 100  # Optional: Limit max size
    
    # Get likes for the post, order by the newest first
    likes = Like.objects.filter(post=post).order_by('-published')
    
    # Paginate the likes
    paginated_likes = paginator.paginate_queryset(likes, request)
    
    # Serialize the paginated likes
    serialized_likes = LikeSerializer(paginated_likes, many=True).data
    
    # Return the paginated response
    likes_count = likes.count()
    node_url = "http://maroonnode.com"
    return paginator.get_paginated_response({
        "type": "likes",
        "page": f"{node_url}/authors/{author_uuid}/posts/{post_id}",
        "id": f"{node_url}/api/authors/{author_uuid}/posts/{post_id}/likes",
        "page_number": paginator.page.number,
        "size": paginator.page.paginator.per_page,
        "count": likes_count,
        "src": serialized_likes,
    })

@extend_schema(
    description=("Get likes by an author.\n"
        "This endpoint allows you to retrieve a paginated list of like objects (for posts or comments) "
        "that were made by a specific author.\n"
        "- **When to use**: Use this endpoint when you want to retrieve a list of likes made by an author.\n"
        "- **How to use**: Make a GET request to `api/authors/{author_uuid}/liked`.\n"
        "- **Why to use**: Useful when clients need to fetch all likes made by a specific author, with support for pagination.\n"
        "- **Why not use**: Avoid using this endpoint if you only need details about a single like."),
    responses={
        200: {
            "type": "object",
            "properties": {
                "type": {"type": "string", "example": "likes"},
                "page": {"type": "string", "example": "http://maroonnode.com/authors/222/posts/249"},
                "id": {"type": "string", "example": "http://maroonnode.com/api/authors/222/posts/249/likes"},
                "page_number": {"type": "integer", "example": 1},
                "size": {"type": "integer", "example": 50},
                "count": {"type": "integer", "example": 9001},
                "src": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "example": "like"},
                            "author": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "example": "author"},
                                    "id": {"type": "string", "example": "http://maroonnode.com/api/authors/48c0840c-40b1-4ff5-a9bc-f410ecdd91b8"},
                                    "page": {"type": "string", "example": "http://maroonnode.com/authors/48c0840c-40b1-4ff5-a9bc-f410ecdd91b8"},
                                    "host": {"type": "string", "example": "http://maroonnode.com/api/"},
                                    "displayName": {"type": "string", "example": "Auro Bee"},
                                    "github": {"type": "string", "example": "http://github.com/aurb"},
                                    "profileImage": {"type": "string", "example": "https://i.imgur.com/k7XVwpB.jpeg"}
                                }
                            },
                            "published": {"type": "string", "example": "2015-03-09T13:07:04+00:00"},
                            "id": {"type": "string", "example": "http://maroonnode.com/api/authors/111/liked/166"},
                            "object": {"type": "string", "example": "http://maroonnode.com/authors/222/posts/249"}
                        }
                    }
                }
            }
        }
    },
    parameters=[
        OpenApiParameter('size', OpenApiTypes.INT, description='Number of likes per page', required=False),
    ],
)
@api_view(['GET'])
def get_likes_by_author(request, author_uuid):
    """
    - Description: Get likes by an author
    - Returns: a paginated list of like objects (for post or comments) for
    a specific author (posts or comments)
    """
    # Get the author by UUID
    author = get_object_or_404(Author, uuid=author_uuid)
    
    # Create a paginator object
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'size'  # Allows user to set ?size= (e.g. ?size=10)
    paginator.page_size = request.GET.get('size', 5)  # Default size: 5
    paginator.max_page_size = 100  # Optional: Limit max size
    
    # Get likes for the author, ordered by the newest first
    likes = Like.objects.filter(author=author).order_by('-published')
    
    # Paginate the likes
    paginated_likes = paginator.paginate_queryset(likes, request)
    
    # Serialize the paginated likes
    serialized_likes = LikeSerializer(paginated_likes, many=True).data
    
    
    # Return the paginated response with the additional fields, including count
    likes_count = likes.count()
    node_url = "http://maroonnode.com"
    return paginator.get_paginated_response({
        "type": "likes",
        "page": f"{node_url}/authors/{author_uuid}/liked",
        "id": f"{node_url}/api/authors/{author_uuid}/liked",
        "page_number": paginator.page.number,
        "size": paginator.page.paginator.per_page,
        "count": likes_count, 
        "src": serialized_likes,
    })


@extend_schema(
    description=(
        "Get a single like object by an author.\n"
        "This endpoint allows you to retrieve a specific like that an author has made, identified by the `like_uuid`.\n"
        "- **When to use**: When you need to fetch a particular like made by an author.\n"
        "- **How to use**: Make a GET request to `/authors/{author_uuid}/liked/{like_uuid}`.\n"
        "- **Why to use**: Useful for retrieving the details of a specific like, such as the author who liked an object and what was liked.\n"
        "- **Why not use**: Not for getting all likes by an author"
    ),
    responses={
        200: LikeSerializer,
    }
)
@api_view(['GET'])
def get_single_like(request, author_uuid, like_uuid):
    author = get_object_or_404(Author, uuid=author_uuid)
    
    # Get the like by UUID and ensure it belongs to the specified author
    like = get_object_or_404(Like, uuid=like_uuid, author=author)
    
    # Serialize the like object
    serialized_like = LikeSerializer(like).data
    
    # Return the serialized like data
    return Response(serialized_like)


### Comments ###

@api_view(['POST'])
@login_required
def add_comment(request, post_id):
    '''
    Add a comment to a post
    '''
    post = get_object_or_404(Post, id=post_id)
    comment_text = request.POST.get('comment')
    content_type = request.POST.get('contentType')
    comment = Comment.objects.create(author=request.user, post=post, comment=comment_text, contentType=content_type)
    comment.id = f"{request.user.id}/commented/{comment.uuid}"
    comment.save()
    return redirect("SocialDistribution:view-single-post", post_id=post_id)

@api_view(['GET'])
def get_post_comments(request, author_uuid, post_id):
    """
    - Description: Get a list of comments for a specified post
    - Returns: a paginated list of comments for a specific post
    """
    post = get_object_or_404(Post, id=post_id, author__uuid=author_uuid)
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'size'  # Allows user to set ?size=
    paginator.page_size = request.GET.get('size', 5)  # Default size: 5
    paginator.max_page_size = 100  # Optional: Limit max size
    comments = Comment.objects.filter(post=post).order_by('-published')
    comment_count = comments.count()
    paginated_comments = paginator.paginate_queryset(comments, request)
    serialized_comments = CommentSerializer(paginated_comments, many=True).data

    node_url = "http://maroonnode.com"
    return paginator.get_paginated_response({
        "type": "comments",
        "page": f"{node_url}/authors/{author_uuid}/posts/{post_id}",
        "id": f"{node_url}/api/authors/{author_uuid}/posts/{post_id}/comments",
        "page_number": paginator.page.number,
        "size": paginator.page.paginator.per_page,
        "count": comment_count,
        "src": [comment for comment in serialized_comments],
    })

@api_view(['GET'])
def get_comments_by_author(request, author_uuid):
    """
    Description: Get the list of comments by an author
    Returns: a paginated list of comment objects for a specific author
    """
    author = get_object_or_404(Author, uuid=author_uuid)
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'size'  # Allows user to set ?size=
    paginator.page_size = request.GET.get('size', 5)  # Default size: 5
    paginator.max_page_size = 100  # Optional: Limit max size
    comments = Comment.objects.filter(author=author).order_by('-published')
    paginated_comments = paginator.paginate_queryset(comments, request)
    serialized_comments = CommentSerializer(paginated_comments, many=True).data
    comment_count = comments.count()

    node_url = "http://maroonnode.com"
    return paginator.get_paginated_response({
        "type": "comments",
        # TODO: page and id might be different because all these comments might not be on the same post
        # "page": f"{node_url}/authors/{author_uuid}/posts/{post_id}",
        # "id": f"{node_url}/api/authors/{author_uuid}/posts/{post_id}/comments",
        "page_number": paginator.page.number,
        "size": paginator.page.paginator.per_page,
        "count": comment_count,
        "src": [comment for comment in serialized_comments],
    })

@api_view(['GET'])
def get_single_comment(request, author_uuid, comment_uuid):
    """
    Description: Get a single comment by an author
    Returns: a single comment by a specific author, identified by comment_uuid
    """
    author = get_object_or_404(Author, uuid=author_uuid)
    comment = get_object_or_404(Comment, uuid=comment_uuid, author=author)
    serialized_comment = CommentSerializer(comment).data
    return Response(serialized_comment)

@login_required
def send_post_to_followers(request, post_id):
    """
    Allows users to share a public or unlisted post with their followers.
    """
    # Get the post or return 404 if not found
    post = get_object_or_404(Post, id=post_id)

    # Ensure that only public and unlisted posts can be shared
    if post.visibility not in ["PUBLIC", "UNLISTED"]:
        messages.error(request, "You can only share public or unlisted posts.")
        return redirect("SocialDistribution:view-single-post", post_id=post.id)

    # Get the logged-in user's followers
    followers = Author.objects.filter(
        uuid__in=FollowRequest.objects.filter(receiver=request.user, status='ACCEPTED')
        .values_list('sender__uuid', flat=True)
    )

    # Send the post title & link to each follower's inbox
    for follower in followers:
        InboxPost.objects.create(receiver=follower, post=post)

    # Show a success message
    messages.success(request, "Shared to followers!")

    # Redirect back to the post page after sharing
    return redirect("SocialDistribution:view-single-post", post_id=post.id)


@login_required
def view_inbox(request):
    """
    Display all posts received in the inbox.
    """
    inbox_posts = InboxPost.objects.filter(receiver=request.user).order_by('-received_at')
    return render(request, "inbox.html", {"inbox_posts": inbox_posts})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_author(request):
    if request.method == "POST":
        form = AuthorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            new_author = form.save()
            return redirect("SocialDistribution:view-profile", uuid=new_author.uuid)
    else:
        form = AuthorRegistrationForm()
    return render(request, "add_author.html", {"form": form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_author_profile(request, uuid):
    '''
    Renders edit author profile page
    '''
    author = get_object_or_404(Author, uuid=uuid)
    if request.method == "POST":
        form = AuthorRegistrationForm(request.POST, request.FILES, instance=author)
        if form.is_valid():
            form.save()
            return redirect("SocialDistribution:view-profile", uuid=author.uuid)
    else:
        form = AuthorRegistrationForm(instance=author)
    return render(request, "edit_author_profile.html", {"form": form, "author": author})

@login_required
@user_passes_test(lambda u: u.is_superuser)
@api_view(['POST'])
def delete_author(request, uuid):
    '''
    Deletes an author
    '''
    author = get_object_or_404(Author, uuid=uuid)
    if request.method == 'POST':
        author.delete()
        return redirect("SocialDistribution:authors_list")
    return render(request, "delete_author.html", {"author": author})
