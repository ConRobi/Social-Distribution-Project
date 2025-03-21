import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from SocialDistribution.models  import Author, Post
from django.contrib.auth import get_user_model


class PostAPITests(APITestCase):
    def setUp(self):
        # Create an author (using the Django User model)
        self.author = Author.objects.create_user(
            username="testuser",
            password="testpassword",
            display_name="Test User",
            host="http://testhost.com",
            id="http://testhost.com/api/authors/testuser",  # You can leave id as a custom value.
            uuid=uuid.uuid4()  # Let Django generate a valid UUID for testing
        )

        self.author2 = Author.objects.create_user(
            username="testuser2",
            password="testpassword12",
            display_name="Test User2",
            host="http://testhost.com",
            id="http://testhost.com/api/authors/testuser2",  # You can leave id as a custom value.
            uuid=uuid.uuid4()  # Let Django generate a valid UUID for testing
        )

        # Authenticate API client
        self.client.login(username="testuser", password="testpassword")

        # Sample friends-only post
        self.post_test = Post.objects.create(
            uuid=uuid.uuid4(),
            title="Test Post",
            description="This is a test post.",
            contentType="text/plain",
            content="Hello, world!",
            author=self.author2,
            visibility="FRIENDS"
        )
        self.node_url = "http://maroonnode.com"
        self.post_test.id = f"{self.node_url}/api/authors/{self.author.uuid}/posts/{self.post_test.uuid}"
        self.post_test.save()

        self.friends_post_view_url = reverse('SocialDistribution:view-single-post', args=[self.post_test.uuid])

    def test_create_post(self):
        """Test creating a valid post"""
        # Define data for creating a post
        post_data = {
            'title': 'Test API Post',
            'description': 'This is a test API post.',
            'contentType': 'text/markdown',
            'content': '## This is markdown content for test post.',
            'visibility': 'PUBLIC',
        }

        # Make POST request to create post
        response = self.client.post(reverse('SocialDistribution:add-post', kwargs={'uuid': self.author.uuid}),
                                    post_data, format='json')

        # Verify response status is HTTP 302 (redirect after successful post creation)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # Check if the post has been created in the database
        post = Post.objects.last()
        self.assertEqual(post.title, 'Test API Post')
        self.assertEqual(post.description, 'This is a test API post.')
        self.assertEqual(post.content, '## This is markdown content for test post.')
        self.assertEqual(post.author, self.author)

    def test_create_post_unauthenticated(self):
        """Test creating post when not logged in"""
        # Logout user to test unauthenticated request
        self.client.logout()

        # Define data for creating a post
        post_data = {
            'title': 'Unauthorized Post',
            'description': 'This post should not be created.',
            'contentType': 'text/markdown',
            'content': '## Unauthorized content.',
            'visibility': 'PUBLIC',
        }

        # Make POST request to create post without authentication
        response = self.client.post(reverse('SocialDistribution:add-post', kwargs={'uuid': self.author.uuid}),
                                    post_data, format='json')

        # Expecting a 302 redirect to login page because the user is unauthenticated
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)


    def test_invalid_post_data(self):
        """Test creating an invalid post"""
        # Define invalid data for creating a post (missing title)
        post_data = {
            'title': '',  # Title is empty, which should be invalid
            'description': 'This post has an invalid title.',
            'contentType': 'text/markdown',
            'content': '## Invalid content.',
            'visibility': 'PUBLIC',
        }

        # Make POST request to create the post with invalid data
        response = self.client.post(reverse('SocialDistribution:add-post', kwargs={'uuid': self.author.uuid}),
                                    post_data, format='json')

        # Verify response status is HTTP 400 (Bad Request) for invalid data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)  # Check if title field is in the errors
    
    def test_user_cannot_access_friends_only_post(self):
        """Test accessing a friends-only post when not following the post author"""
        response = self.client.get(self.friends_post_view_url)

        # The user should not be able to access author2's friends-only post (they are not following each other)
        self.assertEqual(response.status_code, 302)  # Should redirect, unauthorized action