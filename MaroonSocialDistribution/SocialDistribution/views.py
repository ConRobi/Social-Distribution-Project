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
import urllib
import requests

def index(request):
    return render(request, "index.html")



