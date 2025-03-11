from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from models import Author, Post
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponseForbidden
from serializers import PostSerializer

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

### Unlisted Posting ###
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