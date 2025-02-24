from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from SocialDistribution.models import Author, FollowRequest
from django.contrib.auth import get_user_model

User = get_user_model()

class FollowSystemAPITestCase(APITestCase):

    def setUp(self):
        """Create test users for following/followers/friends tests"""
        self.author1 = Author.objects.create_user(username="author1", password="testpass")
        self.author2 = Author.objects.create_user(username="author2", password="testpass")
        self.author3 = Author.objects.create_user(username="author3", password="testpass")

        self.client.login(username="author1", password="testpass")

    def test_send_follow_request(self):
        """Test that an author can send a follow request"""
        url = reverse("SocialDistribution:send-follow-request", args=[self.author2.uuid])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # Redirect after request
        
        follow_request_exists = FollowRequest.objects.filter(sender=self.author1, receiver=self.author2, status="PENDING").exists()
        self.assertTrue(follow_request_exists)

    def test_accept_follow_request(self):
        """Test accepting a follow request"""
        FollowRequest.objects.create(sender=self.author1, receiver=self.author2, status="PENDING")

        self.client.login(username="author2", password="testpass")
        url = reverse("SocialDistribution:accept-follow-request", args=[self.author1.uuid])
        response = self.client.post(url)  # Accept request
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # Redirect expected

        follow_request = FollowRequest.objects.get(sender=self.author1, receiver=self.author2)
        self.assertEqual(follow_request.status, "ACCEPTED")

    def test_follower_status(self):
        """Test checking if an author follows another"""
        FollowRequest.objects.create(sender=self.author1, receiver=self.author2, status="ACCEPTED")

        url = reverse("SocialDistribution:check-follow-status", args=[self.author2.uuid, self.author1.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["follower"])
