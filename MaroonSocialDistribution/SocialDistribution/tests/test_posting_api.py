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

        # Authenticate API client
        self.client.login(username="testuser", password="testpassword")

    def test_create_post(self):
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