from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from SocialDistribution.models import (Author, FollowRequest)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from SocialDistribution.serializers import AuthorSerializer, FollowRequestSerializer

@api_view(['GET'])
def followers_list(request, uuid):
    """
    Retrieve the list of followers for an author
    """
    author = get_object_or_404(Author, uuid=uuid)
    followers = Author.objects.filter(follow_requests_received__accepted=True, follow_requests_received__receiver=author)
    serializer = AuthorSerializer(followers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def following_list(request, uuid):
    """
    Retrieve the list of authors that the given author follows
    """
    author = get_object_or_404(Author, uuid=uuid)
    following = Author.objects.filter(follow_requests_sent__accepted=True, follow_requests_sent__sender=author)
    serializer = AuthorSerializer(following, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def friends_list(request, uuid):
    """
    Retrieve the list of mutual followers (friends) for an author
    """
    author = get_object_or_404(Author, uuid=uuid)
    friends = Author.objects.filter(
        Q(follow_requests_received__accepted=True, follow_requests_received__receiver=author, follow_requests_received__sender__follow_requests_sent__accepted=True, follow_requests_received__sender__follow_requests_sent__receiver=author)
    )
    serializer = AuthorSerializer(friends, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def send_follow_request(request, uuid):
    """
    Send a follow request to another author.
    """
    sender = request.user  # FIX: Use request.user directly, since Author extends AbstractUser
    receiver = get_object_or_404(Author, uuid=uuid)

    if sender == receiver:
        return redirect("SocialDistribution:view-profile", uuid=sender.uuid)  # Prevent self-following

    # Check if a follow request already exists
    follow_request, created = FollowRequest.objects.get_or_create(
        sender=sender,
        receiver=receiver,
        defaults={'status': 'PENDING'}
    )

    return redirect("SocialDistribution:view-profile", uuid=sender.uuid)



@api_view(['GET'])
def check_follow_status(request, uuid, foreign_author_uuid):
    """
    Check if an author follows another
    """
    author = get_object_or_404(Author, uuid=uuid)
    foreign_author = get_object_or_404(Author, uuid=foreign_author_uuid)
    
    is_follower = FollowRequest.objects.filter(sender=foreign_author, receiver=author, status="ACCEPTED").exists()
    
    if is_follower:
        return Response({"follower": True}, status=status.HTTP_200_OK)
    else:
        return Response({"follower": False}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT', 'DELETE'])
def handle_follow_request(request, uuid, sender_uuid):
    """
    Accept or deny a follow request
    """
    receiver = get_object_or_404(Author, uuid=uuid)
    sender = get_object_or_404(Author, uuid=sender_uuid)
    
    follow_request = get_object_or_404(FollowRequest, sender=sender, receiver=receiver)
    
    if request.method == 'PUT':  # Accept request
        follow_request.accepted = True
        follow_request.save()
        return Response({"message": "Follow request accepted."}, status=status.HTTP_200_OK)
    
    if request.method == 'DELETE':  # Deny request
        follow_request.delete()
        return Response({"message": "Follow request denied."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def follow_requests_inbox(request, uuid):
    """
    Retrieve pending follow requests for an author
    """
    author = get_object_or_404(Author, uuid=uuid)
    requests = FollowRequest.objects.filter(receiver=author, accepted=False)
    serializer = FollowRequestSerializer(requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def accept_follow_request(request, sender_uuid):
    """
    Accept a follow request.
    """
    receiver = request.user  # The logged-in user (recipient of the request)
    sender = get_object_or_404(Author, uuid=sender_uuid)
    
    follow_request = get_object_or_404(FollowRequest, sender=sender, receiver=receiver, status='PENDING')
    follow_request.status = 'ACCEPTED'
    follow_request.save()

    return redirect("SocialDistribution:view-profile", uuid=receiver.uuid)

def reject_follow_request(request, sender_uuid):
    """
    Reject a follow request.
    """
    receiver = request.user  # The logged-in user (recipient of the request)
    sender = get_object_or_404(Author, uuid=sender_uuid)

    follow_request = get_object_or_404(FollowRequest, sender=sender, receiver=receiver, status='PENDING')
    follow_request.delete()  # Remove the follow request

    return redirect("SocialDistribution:view-profile", uuid=receiver.uuid)

def follow_requests(request):
    """
    Display pending follow requests on a separate page.
    """
    user = request.user
    follow_requests = FollowRequest.objects.filter(receiver=user, status='PENDING')

    return render(request, "follow_requests.html", {"follow_requests": follow_requests})


def view_followers(request):
    """
    Display the list of followers on a separate page.
    """
    user = request.user
    followers = user.get_followers()
    return render(request, "followers.html", {"followers": followers})

def view_following(request):
    """
    Display the list of users the current user is following.
    """
    user = request.user
    following = user.get_following()
    return render(request, "following.html", {"following": following})

def view_friends(request):
    """
    Display the list of mutual followers (friends).
    """
    user = request.user
    friends = user.get_friends()
    return render(request, "friends.html", {"friends": friends})

def unfollow_user(request, uuid):
    """
    Unfollow a user.
    """
    if request.method == "POST":
        user = request.user
        to_unfollow = get_object_or_404(Author, uuid=uuid)

        # Delete follow request where the current user is the sender and the target user is the receiver
        FollowRequest.objects.filter(sender=user, receiver=to_unfollow, status="ACCEPTED").delete()

    return redirect("SocialDistribution:view-following")


def remove_follower(request, uuid):
    """
    Remove a follower 
    """
    if request.method == "POST":
        user = request.user
        to_remove = get_object_or_404(Author, uuid=uuid)

        # Delete follow request where current user is the receiver and the target user is the sender
        FollowRequest.objects.filter(sender=to_remove, receiver=user, status="ACCEPTED").delete()

    return redirect("SocialDistribution:view-followers")