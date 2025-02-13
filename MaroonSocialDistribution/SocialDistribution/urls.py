from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # Create profile interface page
    path("create-profile", views.create_profile, name="create-profile"),
    # API endpoint for adding profile
    path("add-profile", views.add_profile, name = "add-profile")
]