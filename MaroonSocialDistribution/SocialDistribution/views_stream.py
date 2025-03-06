from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, FollowRequest, InboxPost

@login_required
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
    inbox_posts = Post.objects.filter(id__in=InboxPost.objects.filter(receiver=author).values_list('post_id', flat=True))

    # Merge all posts into a single QuerySet
    all_posts = public_posts.union(friends_posts, unlisted_posts, own_posts, inbox_posts).order_by('-published')

    return render(request, "stream.html", {"posts": all_posts})
