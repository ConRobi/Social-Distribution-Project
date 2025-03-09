from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import Author, Post, FollowRequest, Like, Comment, InboxPost
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
from django.contrib.auth.decorators import login_required



from .serializers import AuthorSerializer, PostSerializer, FollowRequestSerializer


def index(request):
    return render(request, "index.html")

def create_profile(request):
    '''
    Renders create profile page
    '''
    form = AuthorRegistrationForm()
    return render(request, 'create_profile.html', {'form': form})

@api_view(['POST'])
def add_profile(request):
    '''
    Add profile POST request called when create-profile form is submitted.
    Adds a new author profile to database.
    '''

    # Get submitted form fields
    form = AuthorRegistrationForm(request.POST, request.FILES)
    if form.is_valid():
    # Save the form and create a new Author object
        new_author = form.save()
        login(request, new_author)
    

        # TODO GET request to other nodes to see if UUID is unique across all nodes
        # Option 1: Implement check method in models.py, call method in add_profile --> reusable across app
        # Option 2: Implement check in add_profile --> only lives inside add_profile function'
        
        # Create URL based fields based on UUID
        node_url = "http://maroonnode.com"  # TODO need to prefix /SocialDistribution with node eg. node1/SocialDistribution
        new_author.id = f"{node_url}/api/authors/{new_author.uuid}" 
        new_author.host = f"{node_url}/api" 
        new_author.page = f"{node_url}/authors/{new_author.uuid}"

        new_author.save()

        # Redirect to view profile
        return redirect("SocialDistribution:view-profile", uuid=new_author.uuid)
    
    # Render form again with validation errors if sign-up fails
    return render(request, "create_profile.html", {"form": form})

def view_profile(request, uuid):
    ''' View profile page with uuid as url path'''

    author = get_object_or_404(Author, uuid=uuid)
    # Get recent github public activity and display as post
    # TODO add this to stream page instead (fetch when stream is reloaded)
    # TODO add error handling if github link is not valid? or handle that in profile creation/editing?
    try:
        fetch_github_activity(author)
    except Exception as e:
        pass # Ignore error for now

    # Retrieve followers, following, and friends
    followers = author.get_followers()
    following = author.get_following()
    friends = author.get_friends()

    # Retrieve pending follow requests
    follow_requests = FollowRequest.objects.filter(receiver=author, status='PENDING')

    # Fetch posts based on author and visibility (most recent first)
   # Fetch posts based on author and visibility (most recent first)
    if request.user == author:  
        # Show all posts including unlisted (excluding deleted)
        author_posts = Post.objects.filter(author=author).exclude(visibility__iexact='deleted').order_by('-published')
    elif (request.user in followers) and (request.user in following):
        # Show friends-only, public, and unlisted posts
        author_posts = Post.objects.filter(author=author).filter(
            Q(visibility__iexact='friends') | 
            Q(visibility__iexact='friends only') | 
            Q(visibility__iexact='public') | 
            Q(unlisted=True)  # Include unlisted posts
        ).order_by('-published')
    else:
        # Show public and unlisted posts
        # Show only public and unlisted posts
        author_posts = Post.objects.filter(
            Q(author=author, visibility__iexact='public') | 
            Q(author=author, visibility__iexact='unlisted')
        ).order_by('-published')

    # Handle author search functionality
    search_results = None
    query = request.GET.get('query')
    if query:
        search_results = Author.objects.filter(Q(display_name__icontains=query) | Q(username__icontains=query))

    return render(request, "view_profile.html", {
        "author": author,
        "posts": author_posts,
        "followers": followers,
        "following": following,
        "friends": friends,
        "follow_requests": follow_requests,
        "search_results": search_results
    })

@api_view(['GET'])
def authors_list(request):
    authors = Author.objects.all()
    
    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'size'  # Allows user to set ?size=
    paginator.page_size = request.GET.get('size', 5)  # Default size: 5
    paginator.max_page_size = 100  # Optional: Limit max size

    paginated_authors = paginator.paginate_queryset(authors, request)

    # Serialize paginated data
    serializer = AuthorSerializer(paginated_authors, many=True)

    # Return paginated response
    return paginator.get_paginated_response(serializer.data)

def author_login(request):
    '''
    Log in existing users using Django's built-in login authentication
    '''
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Get the username and password from the form and authenticate the author
            author = form.get_user()
            login(request, author)  # Log the author in

            # Redirect to view profile page
            url = f"authors/{author.uuid}"
            return redirect(url)
        else:
            # If the form is invalid, display an error message
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def author_logout(request):
    '''
    Allows a user to be logged out (unauthenticated). Redirects the user to the login page in either case 
    of being logged in or not. Error message is displayed if user is not logged in to begin with.
    '''
    if request.user.is_authenticated:
        logout(request)  
    else:
        messages.warning(request, "You are not logged in.")
    return redirect("SocialDistribution:author-login")

def edit_profile(request, uuid):
    '''
    Renders edit profile page
    '''
    author = get_object_or_404(Author, uuid=uuid)
    return render(request, "edit_profile.html", {"author": author})

@api_view(['GET', 'POST'])
def author_profile(request, uuid):
    '''
    Edit profile using POST request, called when edit-profile form is submitted.
    Updates author fields if new input is provided to them.

    GET request, gets a single author's profile details.
    '''
    
    if request.method == "GET":
        # Return the single author's details in serialized JSON format
        author = get_object_or_404(Author, uuid=uuid)

        serializer = AuthorSerializer(author)

        return Response(serializer.data)
    
    if request.method == "POST":
        
        author = get_object_or_404(Author, uuid=uuid)

        # Update display_name if new display name is provided
        author.display_name = request.POST.get("display_name")

        # Update github if new github url is provided
        author.github = request.POST.get("github")

        # Update profile picture if new profile photo given
        author.profile_image = request.POST.get("profile_image")

        author.save()

        # redirect back to view profile page
        return HttpResponseRedirect(reverse("SocialDistribution:view-profile", args=(author.uuid,)))


""" POSTING """

def author_posts(request, uuid):
    '''
    Renders author posts page
    '''
    author = get_object_or_404(Author, uuid=uuid)
    posts = Post.objects.filter(author=author)
    for post in posts:
        post.rendered_content=post.render_content()
    return render(request, "author_posts.html", {"author": author, "posts": posts})

def create_post(request, uuid):
    '''
    Renders create post page
    '''
    author = get_object_or_404(Author, uuid=uuid)
    return render(request, "create_post.html", {"author": author})

@api_view(['POST'])
def add_post(request, uuid):
    '''
    Add post POST request called when create-post form is submitted.
    Adds a new post to database.
    '''
    author = get_object_or_404(Author, uuid=uuid)

    # Copy request data and add the author UUID
    data = request.data.copy()
    data["author"] = str(author.uuid)  # Pass the correct UUID string
    
    image = request.FILES.get('image')  # Extract image from request

    # Create serializer with BOTH request data and request.FILES
    serializer = PostSerializer(data=data, context={'request': request})

    if serializer.is_valid():
        post = serializer.save()  # Save post first without image

        # Adding image if there is one
        image = request.FILES.get('image')
        if image:
            post.image = image
            post.save()
        return HttpResponseRedirect(reverse("SocialDistribution:view-profile", args=(author.uuid,)))
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST','GET'])
def delete_post(request, author_uuid, post_id):
    """
    Allows an author to delete their post.
    """
    author = get_object_or_404(Author, uuid=author_uuid)
    post = get_object_or_404(Post, id=post_id, author=author)  # Ensure it's an integer lookup

    if request.user != author:
        return HttpResponseForbidden("You are not allowed to delete this post.")
    
    post.visibility = "DELETED"
    post.save()
    return redirect("SocialDistribution:view-profile", uuid=author_uuid) # Redirect to author's profile

@api_view(['POST','GET'])
def edit_post(request, author_uuid, post_id):
    """
    Allows an author to edit their post.
    """
    author = get_object_or_404(Author, uuid=author_uuid)
    post = get_object_or_404(Post, id=post_id, author=author)  # Ensure post belongs to the author

    if request.user != author:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == "POST":
        # Copy request data and ensure all required fields are present
        data = request.POST.copy()
        data["author"] = str(author.uuid)  # Ensure correct author reference

        # Handle visibility properly (don't override if missing)
        if "visibility" not in data:
            data["visibility"] = post.visibility  # Keep previous value

        # Check if the request contains an image
        image = request.FILES.get("image")

        # Use serializer for validation and partial update
        serializer = PostSerializer(post, data=data, partial=True, context={"request": request})

        if serializer.is_valid():
            updated_post = serializer.save()

            # Update image if provided
            if image:
                updated_post.image = image
                updated_post.save()

            return HttpResponseRedirect(reverse("SocialDistribution:view-profile", args=(author.uuid,)))

        return render(request, "edit_post.html", {"post": post, "author": author, "errors": serializer.errors})

    return render(request, "edit_post.html", {"post": post, "author": author})



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
def search_authors(request):
    """
    Search authors by username or display name and render a results page.
    """
    query = request.GET.get("query", "").strip()
    search_results = Author.objects.filter(Q(display_name__icontains=query) | Q(username__icontains=query)) if query else []

    return render(request, "search_results.html", {"search_results": search_results})


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


##################################### unlilsted ################################
@api_view(['GET'])
def view_unlisted_post(request, post_id):
    """
    Allow anyone with the link to view an unlisted post.
    """
    post = get_object_or_404(Post, id=post_id, visibility="UNLISTED")

    serializer = PostSerializer(post)
    return Response(serializer.data, status=status.HTTP_200_OK)

def view_single_post(request, post_id):
    """
    Display a single post, restricting access based on visibility.
    """
    post = get_object_or_404(Post, id=post_id)

    comments = Comment.objects.filter(post=post)
#     return render(request, "single_post.html", {"post": post, "comments": comments})


    # ✅ Allow access if the post is Public or Unlisted (even if not logged in)
    if post.visibility in ["PUBLIC", "UNLISTED"]:
        return render(request, "single_post.html", {"post": post, "comments": comments})

    # ✅ Require authentication for Friends-Only posts
    if post.visibility == "FRIENDS":
        if not request.user.is_authenticated:
            # ❌ Redirect to login if user is not logged in
            messages.error(request, "Unable to view this post. Please log in.")
            return redirect("SocialDistribution:author-login")

        # ✅ Check if the user is a mutual friend
        is_friend = FollowRequest.objects.filter(
            sender=request.user, receiver=post.author, status="ACCEPTED"
        ).exists() and FollowRequest.objects.filter(
            sender=post.author, receiver=request.user, status="ACCEPTED"
        ).exists()

        if is_friend or (request.user == post.author):
            return render(request, "single_post.html", {"post": post})

        # ❌ Show error if user is not a friend
        messages.error(request, "Unable to view this post. You must be friends with the author.")
        return redirect("SocialDistribution:view-profile", request.user.uuid)

    # ❌ If visibility does not match any expected cases, deny access
    messages.error(request, "Unable to view this post.")
    return redirect("SocialDistribution:index")



##################################### unlilsted ends ################################

@login_required
def like_post(request, post_id):
    '''
    Like a post
    Returns a Json Response with the post's like count
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
        new_like.save()
        print(new_like.id)
        print(new_like.uuid)
    else:
        # Remove like if already liked
        like.delete()
    
    # Return the new like count as a JSON response for use in Javascript
    return JsonResponse({'likes_count': post.likes.count()})


### Comments ###

@login_required
def add_comment(request, post_id):
    '''
    Add a comment to a post
    '''
    post = get_object_or_404(Post, id=post_id)
    comment_text = request.POST.get('comment')
    content_type = request.POST.get('contentType')
    Comment.objects.create(author=request.user, post=post, comment=comment_text, contentType=content_type)
    return redirect("SocialDistribution:view-single-post", post_id=post_id)

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


