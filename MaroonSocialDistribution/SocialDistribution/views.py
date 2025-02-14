from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from .models import Author
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


def index(request):
    return render(request, "index.html")

def create_profile(request):
    '''
    Renders create profile page
    '''

    return render(request, "create_profile.html")

@api_view(['POST'])
def add_profile(request):
    '''
    Add profile POST request called when create-profile form is submitted.
    Adds a new author profile to database.
    '''
    
    # Get submitted form fields
    display_name = request.POST.get("display_name")
    github = request.POST.get("github")
    profile_image = request.POST.get("profile_image")  

    # TODO GET request to other nodes to see if UUID is unique across all nodes
    # Option 1: Implement check method in models.py, call method in add_profile --> reusable across app
    # Option 2: Implement check in add_profile --> only lives inside add_profile function'

    # TODO pending admin approval before profile becomes activated

    # Write new author to db
    new_author = Author.objects.create(display_name=display_name, profile_image=profile_image, github=github)
    
    # Create db field "page" URL based on UUID
    # TODO need to prefix /SocialDistribution with node eg. node1/SocialDistribution
    new_author.page = f"/SocialDistribution/authors/{new_author.uuid}"

    # Redirect to view profile
    url = f"authors/{new_author.uuid}"
    return redirect(url)

def view_profile(request, uuid):
    ''' View profile page with uuid as url path'''

    author = get_object_or_404(Author, uuid=uuid)
    return render(request, "view_profile.html", {"author": author})
