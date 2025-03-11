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
    admin_approval = get_object_or_404(AdminApproval, id=1)
    print(admin_approval.require_approval)
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Get the username and password from the form and authenticate the author
            author = form.get_user()
            
            # Admin approval function ON
            if admin_approval.require_approval:
                # Get author object
                author_object = get_object_or_404(Author, display_name=author)
                if not author_object.is_approved:
                    return HttpResponse("Need Admin to approve your account before Logging in")
                else:
                    login(request, author)  # Log the author in
                    # Redirect to view profile page
                    url = f"authors/{author.uuid}"
                    return redirect(url)
                
            # Admin approval function OFF
            else: # Login as normal
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

@api_view['GET']
def author_profile_fqid(request, fqid):
    '''
    Function for getting author's profile based of FQID 
    '''

    if request == "GET":
        

    pass


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
@extend_schema(
    summary="Retrieve an unlisted post",
    description="""
    This endpoint allows **anyone with the link** to retrieve an unlisted post.  
    - ✅ No authentication required.
    - ✅ Anyone with the link can view it.
    - ❌ Not recommended for private posts.
    """,
    parameters=[
        {
            "name": "post_id",
            "description": "The ID of the unlisted post to retrieve.",
            "required": True,
            "type": "integer",
        }
    ],
    responses={
        200: PostSerializer,
        404: {"detail": "Not found"},
    },
    examples=[
        OpenApiExample(
            "Successful Response",
            value={
                "id": 2,
                "title": "Unlisted Post",
                "content": "This is an unlisted post",
                "visibility": "UNLISTED",
                "author_id": "6bde6334-a6be-4c6c-baa1-19f7371cf879",
                "published": "2025-03-10T05:13:35.137044Z",
            },
            response_only=True,
        ),
        OpenApiExample(
            "Not Found",
            value={"detail": "Not found"},
            response_only=True,
            status_codes=["404"],
        ),
    ],
)
@api_view(["GET"])
def view_unlisted_post(request, post_id):
    """
    Allow anyone with the link to view an unlisted post.
    SECURITY WARNING: This API is **not private**. Anyone with the link can see the post.
    """
    post = get_object_or_404(Post, id=post_id, visibility="UNLISTED")

    serializer = PostSerializer(post)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Retrieve a single post",
    description="""
    This endpoint retrieves a single post and **restricts access** based on its visibility:  
    - ✅ **PUBLIC & UNLISTED**: Anyone can view it.  
    - ✅ **FRIENDS-ONLY**: Requires authentication. Only the author & mutual friends can see it.  
    - ❌ **Others**: Unauthorized users are redirected.  
    """,
    parameters=[
        {
            "name": "post_id",
            "description": "The ID of the post to retrieve.",
            "required": True,
            "type": "integer",
        }
    ],
    responses={
        200: PostSerializer,
        302: {"detail": "Redirected due to permission restrictions"},
        404: {"detail": "Not found"},
    },
    examples=[
        OpenApiExample(
            "Public Post",
            value={
                "id": 1,
                "title": "Public Post",
                "content": "This is a public post",
                "visibility": "PUBLIC",
                "author_id": "a1b2c3d4-5678-9101-1121-314151617181",
                "published": "2025-03-10T05:13:35.137044Z",
            },
            response_only=True,
        ),
        OpenApiExample(
            "Friends-Only Post (Access Denied)",
            value={"detail": "You must be friends with the author to view this post."},
            response_only=True,
            status_codes=["302"],
        ),
        OpenApiExample(
            "Not Found",
            value={"detail": "Not found"},
            response_only=True,
            status_codes=["404"],
        ),
    ],
)
@api_view(["GET", "POST"])
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
            return render(request, "single_post.html", {"post": post, "comments": comments})

        # ❌ Show error if user is not a friend
        messages.error(request, "Unable to view this post. You must be friends with the author.")
        return redirect("SocialDistribution:view-profile", request.user.uuid)

    # ❌ If visibility does not match any expected cases, deny access
    messages.error(request, "Unable to view this post.")
    return redirect("SocialDistribution:index")



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
