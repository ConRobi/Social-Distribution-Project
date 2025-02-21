from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from .models import Author, Post
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, authenticate
from .forms import AuthorRegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages


from .serializers import AuthorSerializer, PostSerializer


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

        # TODO pending admin approval before profile becomes activated

        
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
    # Get public posts made by the author (most recent posts first)
    public_posts = Post.objects.filter(author=author, visibility__iexact='public').order_by('-published')
    return render(request, "view_profile.html", {"author": author, "posts": public_posts})

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
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Get the username and password from the form and authenticate the user
            author = form.get_user()
            login(request, author)  # Log the user in

            # Redirect to view profile page
            url = f"authors/{author.uuid}"
            return redirect(url)
        else:
            # If the form is invalid, display an error message
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def edit_profile(request, uuid):
    '''
    Renders edit profile page
    '''
    author = get_object_or_404(Author, uuid=uuid)
    return render(request, "edit_profile.html", {"author": author})

@api_view(['POST'])
def update_profile(request, uuid):
    '''
    Edit profile POST request called when edit-profile form is submitted.
    Updates author fields if new input is provided to them.
    '''
    author = get_object_or_404(Author, uuid=uuid)
    profile_image_url = request.POST.get("profile_image")
    # if a new image url is provided, set it to corresponding field
    # TODO need to handle saving profile image uploaded as url??
    if profile_image_url:
        author.profile_image = profile_image_url

    # update display_name if new display name is provided
    author.display_name = request.POST.get("display_name")

    # update github if new github url is provided
    author.github = request.POST.get("github")

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

    title = request.POST.get("title")
    description = request.POST.get("description")
    content = request.POST.get("content")
    visibility = request.POST.get("visibility")

    new_post = Post.objects.create(
        title=title,
        description=description,
        content=content,
        visibility=visibility,
        author=author  # Associate the post with the author
    )

    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return HttpResponseRedirect(reverse("SocialDistribution:view-profile", args=(author.uuid,)))