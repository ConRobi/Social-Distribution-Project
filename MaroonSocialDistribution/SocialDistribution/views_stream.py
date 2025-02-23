from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Post, FollowRequest, InboxPost

@login_required
def stream_view(request):
    """Fetch posts for the stream page, ordered by latest first."""

    # Get the logged-in author
    author = request.user

    # Get all public posts (excluding deleted & unlisted)
    public_posts = Post.objects.filter(visibility="PUBLIC").exclude(visibility="DELETED")

    # Get authors that this user follows
    following_authors = FollowRequest.objects.filter(
        sender=author, status="ACCEPTED"
    ).values_list("receiver", flat=True)

    # Get authors who also follow this user (mutual friends)
    mutual_friends = FollowRequest.objects.filter(
        sender__in=following_authors, receiver=author, status="ACCEPTED"
    ).values_list("sender", flat=True)

    # Get friends-only posts from mutual friends
    friends_posts = Post.objects.filter(author__in=mutual_friends, visibility="FRIENDS")

    # Get the user's own posts (so they always see their posts)
    own_posts = Post.objects.filter(author=author).exclude(visibility="DELETED")

    # Get posts received in the inbox (from other nodes)
    inbox_posts = Post.objects.filter(id__in=InboxPost.objects.filter(receiver=author).values_list('post_id', flat=True))

    # Apply filtering before union (to avoid issues with .exclude())
    public_posts = public_posts.exclude(visibility="UNLISTED")
    friends_posts = friends_posts.exclude(visibility="UNLISTED")
    own_posts = own_posts.exclude(visibility="UNLISTED")
    inbox_posts = inbox_posts.exclude(visibility="UNLISTED")

    # Merge all posts into a single QuerySet
    all_posts = public_posts.union(friends_posts, own_posts, inbox_posts).order_by('-published')

    return render(request, "stream.html", {"posts": all_posts})
