from rest_framework.test import APITestCase
from rest_framework import status
from SocialDistribution.models import Author, Post, Comment
from django.urls import reverse
from uuid import uuid4

class CommentAPITestCase(APITestCase):
    def setUp(self):
        """
        Create sample author, post, and like objects for testing.
        """
        self.node_url = "http://maroonnode.com"
        self.author = Author.objects.create(
            uuid=uuid4(),
            display_name="Test User",
            github="http://github.com/testuser"
        )
        self.author.host = f"{self.node_url}/api" 
        self.author.id = f"{self.node_url}/api/authors/{self.author.uuid}"
        self.author.page = f"{self.node_url}/authors/{self.author.uuid}"
        self.author.save()

        # Create a post to test
        self.post = Post.objects.create(
            id=10, 
            title="Test Post 10",
            description="This is a test post.",
            contentType="text/plain",
            content="Hello, world!",
            author=self.author,
            visibility="PUBLIC"
        )

        # Authenticate API client
        self.client.login(username="testuser", password="testpassword")
        
        # Create a comment to test
        self.comment1 = Comment.objects.create(uuid=uuid4(), author=self.author, post=self.post, comment="I like this post!", contentType="text/plain")
        self.comment1.id = f"{self.author.id}/posts/{self.post.id}/commented/{self.comment1.uuid}"
        self.comment1.save()

        self.comment2 = Comment.objects.create(uuid=uuid4(), author=self.author, post=self.post, comment="I hate this post!", contentType="text/plain")
        self.comment2.id = f"{self.author.id}/posts/{self.post.id}/commented/{self.comment2.uuid}"
        self.comment2.save()

        # Most recent comment will be at the top (comment 2)

    def test_create_comment(self):
        """
        Testing that the commment information is correct
        """
        self.assertEqual(self.comment1.comment, "I like this post!")
        self.assertEqual(self.comment1.author, self.author)
        self.assertEqual(self.comment1.post, self.post)
    
    def test_get_single_comment(self):
        """
        Testing that the single comment can be retrieved
        """
        url = reverse('SocialDistribution:get_single_comment', kwargs={'author_uuid': self.author.uuid, 'comment_uuid': self.comment1.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comment'], "I like this post!")
        # For author
        self.assertEqual(response.data['author']['id'], self.author.id)
        self.assertEqual(response.data['author']['display_name'], self.author.display_name)
    
    def test_get_comments_by_author(self):
        """
        Testing that the comments by author can be retrieved
        """
        url = reverse('SocialDistribution:get_comments_by_author', kwargs={'author_uuid': self.author.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check both comments created
        comment_list = response.data['results']['src']

        self.assertEqual(comment_list[0]['comment'], "I hate this post!")
        self.assertEqual(comment_list[0]['id'], self.comment2.id)

        self.assertEqual(comment_list[1]['comment'], "I like this post!")
        self.assertEqual(comment_list[1]['id'], self.comment1.id)
        
    def test_get_post_comments(self):
        """
        Testing that the comments for a post can be retrieved
        """
        url = reverse('SocialDistribution:post_comments', kwargs={'author_uuid': self.author.uuid, 'post_id': self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check both comments created
        comment_list = response.data['results']['src']

        self.assertEqual(comment_list[0]['comment'], "I hate this post!")
        self.assertEqual(comment_list[1]['comment'], "I like this post!")
        