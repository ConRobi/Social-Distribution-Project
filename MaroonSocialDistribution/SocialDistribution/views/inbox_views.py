from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from models import InboxPost


@login_required
def view_inbox(request):
    """
    Display all posts received in the inbox.
    """
    inbox_posts = InboxPost.objects.filter(receiver=request.user).order_by('-received_at')
    return render(request, "inbox.html", {"inbox_posts": inbox_posts})
