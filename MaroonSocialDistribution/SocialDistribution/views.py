import urllib

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseRedirect, JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiTypes, extend_schema)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .forms import AuthorRegistrationForm
from .models import (AdminApproval, Author, Comment, FollowRequest, InboxPost,
                     Like, Post)
from .serializers import (AuthorSerializer, CommentSerializer,
                          FollowRequestSerializer, LikeSerializer,
                          PostSerializer)
from .services.github_service import fetch_github_activity


def index(request):
    return render(request, "index.html")



