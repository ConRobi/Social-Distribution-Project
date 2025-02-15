from django.urls import path
from . import views

app_name = 'SocialDistribution'

urlpatterns = [
    path("", views.index, name="index"),
    # Create profile interface page
    path("create-profile", views.create_profile, name="create-profile"),
    # API endpoint for adding profile
    path("add-profile", views.add_profile, name = "add-profile"),
    # View profile page
    path("authors/<uuid:uuid>", views.view_profile, name = "view-profile"),
    path("<uuid:uuid>/edit-profile", views.edit_profile, name = "edit-profile"),
    path("<uuid:uuid>/update-profile", views.update_profile, name = "update-profile")
]