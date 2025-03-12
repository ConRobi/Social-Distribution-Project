from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from SocialDistribution.models import Author, Like, Post, Comment
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

        # Test comment to like 
        self.comment = Comment.objects.create(
            id=200,
            uuid=uuid.uuid4(),
            author=self.author,
            post= self.post,
            comment="hi world",
            contentType="text/plain"

        )

        # Test like for post
        self.like = Like.objects.create(
            uuid=uuid.uuid4(),
            author=self.author,
            post=self.post,
            object=f"{self.node_url}/api/authors/{self.author.uuid}/posts/{self.post.id}"
        )
        self.like.id = f"{self.author.id}/liked/{self.like.uuid}"
        self.like.save()

        # Test like for comment
        self.like2 = Like.objects.create(
            uuid=uuid.uuid4(),
            author=self.author,
            comment=self.comment,
            object=f"{self.node_url}/api/authors/{self.author.uuid}/posts/{self.comment.uuid}"
        )
        self.like2.id = f"{self.author.id}/liked/{self.like2.uuid}"
        self.like2.save()

        self.single_like_url = reverse('SocialDistribution:get_single_like', args=[self.author.uuid, self.like.uuid])
        self.post_likes_url = reverse('SocialDistribution:post_likes', args=[self.author.uuid, self.post.id])
        self.likes_by_author = reverse('SocialDistribution:get_likes_by_author', args=[self.author.uuid])

    def test_get_single_like_success(self):
        """
        Ensure we can retrieve a single like
        """
        print(f"self.single_like_url: {self.single_like_url}")
        response = self.client.get(self.single_like_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.like.id))  # Ensure ID matches

    def test_get_likes_nonexistent_post(self):
        """
        Ensure requesting likes for a non-existent post returns 404
        """
        fake_post_id = 99999  # Must be an integer
        url = reverse('SocialDistribution:post_likes', args=[self.author.uuid, fake_post_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_post_likes(self):
        """
        Ensure we can retrieve a paginated list of likes for a post
        """
        response = self.client.get(self.post_likes_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("src" in response.data["results"])  # Check if "src" key exists
        self.assertEqual(len(response.data["results"]["src"]), 1)  # Created one like for a post in setUp()

    def test_get_author_likes(self):
        """
        Ensure we can retrieve a paginated list of like objects for an author
        """
        response = self.client.get(self.likes_by_author)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]["src"]), 2) # Author liked a comment and post (2 like objects)

    def test_get_author_likes(self):
        """
        Ensure that a list of like objects for an author is empty if likes are removed
        """
        self.like.delete()
        self.like2.delete()
        response = self.client.get(self.likes_by_author)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]["src"]), 0) # removed author likes so it should be 0