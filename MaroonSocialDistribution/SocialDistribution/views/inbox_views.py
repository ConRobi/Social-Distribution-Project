from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from SocialDistribution.models import InboxPost
from rest_framework.decorators import api_view


@login_required
def view_inbox(request):
    """
    Display all posts received in the inbox.
    """
    inbox_posts = InboxPost.objects.filter(receiver=request.user).order_by('-received_at')
    return render(request, "inbox.html", {"inbox_posts": inbox_posts})

# @api_view(['POST'])
# def send_to_inbox(request):
#     """
#     Send a post to the inbox of another author.
#     """
#     sender = request.user
#     receiver = request.data.get('receiver')
#     post = request.data.get('post')

#     inbox_post = InboxPost.objects.create(sender=sender, receiver=receiver, post=post)
#     inbox_post.save()

#     # return Response({"message": "Post sent to inbox."}, status=status.HTTP_200_OK)