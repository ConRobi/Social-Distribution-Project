from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from SocialDistribution.models import Author, Post, FollowRequest, AdminApproval
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, logout
from SocialDistribution.forms import AuthorRegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from SocialDistribution.services.github_service import fetch_github_activity
from SocialDistribution.serializers import AuthorSerializer
import requests
import uuid

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
            Q(visibility__iexact='unlisted')  # Include unlisted posts
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
def search_authors(request):
    """
    Search authors by username or display name and render a results page.
    """
    query = request.GET.get("query", "").strip()
    search_results = Author.objects.filter(Q(display_name__icontains=query) | Q(username__icontains=query)) if query else []

    return render(request, "search_results.html", {"search_results": search_results})


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

    # Ensure the logged-in user is editing their own profile
    if author != request.user:
        # Redirect to profile page
        return redirect('SocialDistribution:view-profile', uuid=author.uuid)

    return render(request, "edit_profile.html", {"author": author})

def is_valid_uuid(value):
    """Helper function to find if the string value is a uuid """
    try:
        uuid.UUID(value, version=4)  # Specify version 4 for standard UUID v4
        return True
    except ValueError:
        return False
    
@api_view(['GET', 'POST'])
def author_profile(request, identifier):
    '''
    Edit profile using POST request, called when edit-profile form is submitted.
    Updates author fields if new input is provided to them.

    GET request, gets a single author's profile details. 
    For local nodes use authors uuid eg /api/authors/Fa7f15b29-98d9-4230-ac75-8594c7f61623
    For remote use a percent encoded author's id url (FQID) eg /api/authors/http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fauthors%2Fa7f15b29-98d9-4230-ac75-8594c7f61623
    '''
    
    if request.method == "GET":
        
        if is_valid_uuid(identifier):
            print(f"uuid: {identifier}")
        # Handle UUID logic
            try:
                # Return the single author's details in serialized JSON format
                author = get_object_or_404(Author, uuid=identifier)

                serializer = AuthorSerializer(author)

                return Response(serializer.data)

            except Author.DoesNotExist:
                raise JsonResponse({"error": "Author not found"}, status=404)
        
        else:
        # Handle FQID logic
            print(f"fqid: {identifier}")
            response = requests.get(identifier)

            if response.status_code == 200:
                author_data = response.json()
                return JsonResponse(author_data)
            
            else:
                return JsonResponse({"error": "Failed to fetch author data"}, status=response.status_code)


    if request.method == "POST":

        author = get_object_or_404(Author, uuid=identifier)

        # Update display_name if new display name is provided
        author.display_name = request.POST.get("display_name")

        # Update github if new github url is provided
        author.github = request.POST.get("github")

        # Update profile picture if new profile photo given
        author.profile_image = request.POST.get("profile_image")

        author.save()

        # redirect back to view profile page
        return HttpResponseRedirect(reverse("SocialDistribution:view-profile", args=(author.uuid,)))

@api_view(['GET'])
def author_profile_fqid(request, fqid):
    '''
    GET request - gets author's profile based on FQID.
    FQID is a percent encoded author's profile id url.
    Example GET request: http://localhost:8000/api/authors/http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fauthors%2Fa7f15b29-98d9-4230-ac75-8594c7f61623
    FQID: http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fauthors%2Fa7f15b29-98d9-4230-ac75-8594c7f61623
    '''
    
    if request.method == "GET":
        response = requests.get(fqid)

        if response.status_code == 200:
            author_data = response.json()
            return JsonResponse(author_data)
        
        else:
            return JsonResponse({"error": "Failed to fetch author data"}, status=response.status_code)
    
    return JsonResponse({"error": "Only GET requests allowed"}, status=404)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_author(request):
    if request.method == "POST":
        print("Post method reached")
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