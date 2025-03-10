from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from SocialDistribution.models import Author, Like, Post
import uuid

class LikeAPITestCase(APITestCase):
    def setUp(self):
        """
        Create sample author, post, and like objects for testing.
        """
        self.node_url = "http://maroonnode.com"
        self.author = Author.objects.create(
            uuid=uuid.uuid4(),
            display_name="Test User",
            github="http://github.com/testuser"
        )
        self.author.host = f"{self.node_url}/api" 
        self.author.id = f"{self.node_url}/api/authors/{self.author.uuid}"
        self.author.page = f"{self.node_url}/authors/{self.author.uuid}"
        self.author.save()

        self.post = Post.objects.create(
            # TODO Maybe change if id becomes url?
            id=200, 
            title="Test Post",
            description="This is a test post.",
            contentType="text/plain",
            content="Hello, world!",
            author=self.author,
            visibility="PUBLIC"
        )

        self.like = Like.objects.create(
            uuid=uuid.uuid4(),
            author=self.author,
            post=self.post,
            object=f"{self.node_url}/api/authors/{self.author.uuid}/posts/{self.post.id}"
        )
        self.like.id = f"{self.author.id}/liked/{self.like.uuid}"
        self.like.save()

        self.single_like_url = reverse('SocialDistribution:get_single_like', args=[self.author.uuid, self.like.uuid])
        self.post_likes_url = reverse('SocialDistribution:post_likes', args=[self.author.uuid, self.post.id])

    def test_get_single_like_success(self):
        """
        Ensure we can retrieve a single like
        """
        response = self.client.get(self.single_like_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.like.id))  # Ensure ID matches

    def test_get_likes_nonexistent_post(self):
        """
        Ensure requesting likes for a non-existent post returns 404.
        """
        fake_post_id = 99999  # Must be an integer
        url = reverse('SocialDistribution:post_likes', args=[self.author.uuid, fake_post_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_post_likes(self):
        """
        Ensure we can retrieve a paginated list of likes for a post.
        """
        response = self.client.get(self.post_likes_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("src" in response.data["results"])  # Check if "src" key exists
        self.assertEqual(len(response.data["results"]["src"]), 1)  # We created one like in setUp()



