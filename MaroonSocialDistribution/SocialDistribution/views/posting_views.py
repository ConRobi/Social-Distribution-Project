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
