from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from .models import Author
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


def index(request):
    return render(request, "index.html")

def create_profile(request):
    return render(request, "create_profile.html")

@api_view(['POST'])
def add_profile(request):
    
    display_name = request.POST.get("display_name")
    github = request.POST.get("github")
    profile_image = request.POST.get("profile_image")

    Author.objects.create(display_name=display_name, profile_image=profile_image, github=github)

    return redirect(reverse("polls:results", kwargs={"pk": profile_image.id}))

def view_profile(request):
    pass