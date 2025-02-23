from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, FollowRequest

@login_required
def stream_view(request):
    """Fetch posts for the stream page, ordered by latest first."""

    # Get the logged-in author
    author = request.user

    # Get all public posts (excluding deleted)
    public_posts = Post.objects.filter(visibility="PUBLIC").exclude(visibility="DELETED")

    # Get authors the user follows
    following_authors = FollowRequest.objects.filter(
        sender=author, status="ACCEPTED"
    ).values_list("receiver", flat=True)

    # Get friends-only and unlisted posts from followed authors
    friends_posts = Post.objects.filter(author__in=following_authors, visibility="FRIENDS")
    unlisted_posts = Post.objects.filter(author__in=following_authors, visibility="UNLISTED")

    # Merge all post queries
    all_posts = public_posts | friends_posts | unlisted_posts

    # Sort posts by latest published date
    all_posts = all_posts.order_by('-published')

    return render(request, "stream.html", {"posts": all_posts})
