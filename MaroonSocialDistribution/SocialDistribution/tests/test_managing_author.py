from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from SocialDistribution.models import Author

User = get_user_model()

class AuthorManagementTests(APITestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username='admin', password='admin123', email='admin@example.com')
        self.client.login(username='admin', password='admin123')
        self.add_author_url = reverse('SocialDistribution:add-author')
        self.edit_author_url = lambda uuid: reverse('SocialDistribution:edit-author-profile', args=[uuid])
        self.delete_author_url = lambda uuid: reverse('SocialDistribution:delete-author', args=[uuid])

    def test_add_author(self):
        """ Test adding a new author. """
        response = self.client.post(self.add_author_url, {
            'username': 'newauthor',
            'display_name': 'New Author',
            'github': 'https://github.com/newauthor',
            'password1': 'password123',
            'password2': 'password123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Author.objects.filter(username='newauthor').exists())

    def test_edit_author(self):
        """ Test editing an existing author. """
        author = Author.objects.create_user(username='editauthor', password='password123', display_name='Edit Author', github='https://github.com/editauthor')
        response = self.client.post(self.edit_author_url(author.uuid), {
            'username': 'editauthor',
            'display_name': 'Edited Author',
            'github': 'https://github.com/editedauthor',
        })
        self.assertEqual(response.status_code, 302)
        author.refresh_from_db()
        self.assertEqual(author.display_name, 'Edited Author')
        self.assertEqual(author.github, 'https://github.com/editedauthor')

    def test_delete_author(self):
        """ Test deleting an author. """
        author = Author.objects.create_user(username='deleteauthor', password='password123', display_name='Delete Author', github='https://github.com/deleteauthor')
        response = self.client.post(self.delete_author_url(author.uuid))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Author.objects.filter(username='deleteauthor').exists())