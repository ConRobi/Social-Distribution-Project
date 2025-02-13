from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, "index.html")

def create_profile(request):
    pass

def view_profile(request):
    pass