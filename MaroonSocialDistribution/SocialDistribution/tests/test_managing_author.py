from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from SocialDistribution.models import Author
from django.utils import timezone
import uuid

class AuthorAdminTests(TestCase):
    
    def setUp(self):
        # Create a superuser for the test
        self.superuser = get_user_model().objects.create_superuser(
            username="admin", password="password"
        )

        self.node_url = "http://maroonnode.com"
        self.author = Author.objects.create(
            uuid=uuid.uuid4(),
            display_name="Test User",
            github="http://github.com/testuser",
            username="testauthor",
            password="verysecurepass12"
        )
        self.author.host = f"{self.node_url}/api" 
        self.author.id = f"{self.node_url}/api/authors/{self.author.uuid}"
        self.author.page = f"{self.node_url}/authors/{self.author.uuid}"
        self.author.save()

        self.client = Client()
        self.client.login(username="admin", password="password")
        
        self.delete_url = reverse('admin:SocialDistribution_author_delete', args=[self.author.uuid])
        self.changelist_url = reverse('admin:SocialDistribution_author_changelist')
        self.add_author_url = reverse('admin:SocialDistribution_author_add')
        self.edit_url = reverse('admin:SocialDistribution_author_change', args=[self.author.uuid])



    def test_create_author_from_admin(self):
        # Prepare data for creating a new Author
        data = {
            'type': 'author',
            'username': 'newauthor',
            'password': 'securepassword123',
            'display_name': 'New Author',
            'github': 'https://github.com/newauthor',
            'profile_image': 'https://example.com/profile.jpg',
            'is_approved': True,
            'last_checked_0': '2025-03-20',  
            'last_checked_1': '01:49:32', 
            'date_joined_0': '2025-03-20',  
            'date_joined_1': '01:49:32',
        }

        # Send a POST request to create the author
        response = self.client.post(self.add_author_url, data)


        # Check that the response redirects to the change list page after creation
        self.assertRedirects(response, self.changelist_url)

        # Check that the Author object was created in the database
        author = Author.objects.get(username='newauthor')
        self.assertEqual(author.display_name, 'New Author')
        self.assertEqual(author.github, 'https://github.com/newauthor')
        self.assertEqual(author.profile_image, 'https://example.com/profile.jpg')
        self.assertTrue(author.is_approved)

        # Verify the password is hashed (not stored as plain text)
        self.assertTrue(author.check_password('securepassword123'))
        self.assertNotEqual(author.password, 'securepassword123')  # Ensure the password is hashed

    def test_admin_can_access_author_add_page(self):
        # Check if the admin user can access the add page
        response = self.client.get(self.add_author_url)
        self.assertEqual(response.status_code, 200)

    def test_author_is_approved_by_default(self):
        # Test if the "is_approved" field is set correctly
        author = Author.objects.create_user(
            username='defaultauthor',
            password='password123',
            display_name='Default Author'
        )

        self.assertFalse(author.is_approved)  # By default, is_approved should be False

    def test_edit_author_in_admin(self):
        """Test editing an author in the Django admin panel."""
        new_data = {
            'type': 'author',
            'username': 'testauthor',
            'display_name': 'Updated Author',
            'password': 'verysecurepass12',
            'github': 'https://github.com/updatedauthor',
            'profile_image': 'https://example.com/newprofile.jpg',
            'is_approved': True,
            'last_checked_0': '2025-03-20',  
            'last_checked_1': '01:49:32', 
            'date_joined_0': '2025-03-20',  
            'date_joined_1': '01:49:32',
        }

        response = self.client.post(self.edit_url, new_data, follow=True)

        # Check if the response redirects correctly
        self.assertRedirects(response, self.changelist_url)

        # Refresh from DB and check if data was updated
        self.author.refresh_from_db()
        self.assertEqual(self.author.display_name, 'Updated Author')
        self.assertEqual(self.author.github, 'https://github.com/updatedauthor')
        self.assertEqual(self.author.profile_image, 'https://example.com/newprofile.jpg')
        self.assertTrue(self.author.is_approved)

    def test_delete_author_in_admin(self):
        """Test deleting an author using the Django admin panel."""
        # Get the delete confirmation page
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)  # Ensure the page loads

        # Confirm deletion (admin delete forms use 'post' with a confirmation)
        response = self.client.post(self.delete_url, {'post': 'yes'}, follow=True)

        # Check if the response redirects correctly
        self.assertRedirects(response, self.changelist_url)

        # Verify that the author is deleted from the database
        with self.assertRaises(Author.DoesNotExist):
            Author.objects.get(username='testauthor')

        # Ensure no authors exist after deletion (not counting the admin)
        self.assertEqual(Author.objects.exclude(username='admin').count(), 0)
