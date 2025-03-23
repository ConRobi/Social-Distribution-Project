from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.decorators import api_view
from django.shortcuts import render
from SocialDistribution.models import Post, FollowRequest, InboxPost


@extend_schema(
    summary="Retrieve a single post with visibility restrictions",
    description="""
    This endpoint displays a **single post** while enforcing visibility rules:

    - ✅ **Public & Unlisted Posts** → Anyone can view.
    - ✅ **Friends-Only Posts** → Requires login + mutual friendship.
    - ❌ **Private Posts** → Redirected with an error.
    """,
    parameters=[
        {
            "name": "post_id",
            "description": "The unique ID of the post to retrieve.",
            "required": True,
            "type": "integer",
        }
    ],
    responses={
        200: "HTML page with post details",
        302: {"detail": "Redirected due to visibility restrictions"},
        404: {"detail": "Post not found"},
    },
    examples=[
        OpenApiExample(
            "Public Post Example",
            value={
                "id": 3,
                "title": "My Public Post",
                "content": "This is a public post!",
                "visibility": "PUBLIC",
                "author_id": "123e4567-e89b-12d3-a456-426614174000",
                "published": "2025-03-10T06:00:00Z",
            },
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "Restricted Access Example",
            value={"detail": "Unable to view this post. You must be friends with the author."},
            response_only=True,
            status_codes=["302"],
        ),
        OpenApiExample(
            "Not Found Example",
            value={"detail": "Not found"},
            response_only=True,
            status_codes=["404"],
        ),
    ],
)
@api_view(["GET"])
def stream_view(request):
    """Fetch posts for the stream page, ordered by latest first."""

    # Get the logged-in author
    author = request.user

    # Get all public posts (excluding deleted)
    public_posts = Post.objects.filter(visibility="PUBLIC").exclude(visibility="DELETED")

    # Get authors that this user follows
    following_authors = FollowRequest.objects.filter(
        sender=author, status="ACCEPTED"
    ).values_list("receiver", flat=True)

    # ✅ Fix: Friends-only posts should appear if the user FOLLOWS the author
    friends_posts = Post.objects.filter(author__in=following_authors, visibility="FRIENDS")

    # ✅ Fix: Unlisted posts should also appear if the user follows the author
    unlisted_posts = Post.objects.filter(author__in=following_authors, visibility="UNLISTED")

    # Get the user's own posts (so they always see their posts)
    own_posts = Post.objects.filter(author=author).exclude(visibility="DELETED")

    # Get posts received in the inbox (from other nodes)
    inbox_posts = Post.objects.filter(uuid__in=InboxPost.objects.filter(receiver=author).values_list('post__uuid', flat=True))

    # Merge all posts into a single QuerySet
    all_posts = public_posts.union(friends_posts, unlisted_posts, own_posts, inbox_posts).order_by('-published')

    return render(request, "stream.html", {"posts": all_posts})
