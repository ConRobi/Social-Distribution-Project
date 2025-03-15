from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from SocialDistribution.models import Author
import uuid

User = get_user_model()

class ProfileAPITestCase(APITestCase):
    
    def setUp(self):
        # Create a test user
        self.user = Author.objects.create_user(
            username="testuser",
            password="testpassword",
            display_name="Test User"
        )
        self.client.login(username="testuser", password="testpassword")

    def test_create_profile(self):
        """ Test creating a new profile. """
        url = reverse("SocialDistribution:add-profile")
        data = {
            "username": "newuser",
            "password": "newpassword",
            "display_name": "New User",
            "github": "https://github.com/newuser",
        }
        response = self.client.post(url, data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
       
    
    def test_view_profile(self):
        """ Test retrieving a user profile by UUID. """
        url = reverse("SocialDistribution:view-profile", args=[self.user.uuid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.user.display_name)
    
    def test_edit_profile_page(self):
        """ Test rendering the edit profile page. """
        url = reverse("SocialDistribution:edit-profile", args=[self.user.uuid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Edit Profile")
    
    def test_update_profile(self):
        """ Test updating a profile. """
        url = reverse("SocialDistribution:author-profile", args=[self.user.uuid])
        data = {
            "display_name": "Updated Name",
            "github": "https://github.com/updateduser"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Updated Name")
        self.assertEqual(self.user.github, "https://github.com/updateduser")
    
    # TODO test edit profile, posts etc as other user