"""Test user app"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')
def create_user(**params):
    """Create and return new user"""
    return get_user_model().objects.create_user(**params)

class PublicUserApiTests(TestCase):
    """Test the public features of user API"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating user is successful"""
        payload = {
            'email' : 'test@example.com',
            'password' : 'password123',
            'name' : 'Test Name',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertEqual(user.name, payload['name'])
        self.assertNotIn('password', res.data)

    def test_create_user_already_exist_error(self):
        payload = {
            'email' : 'test@example.com',
            'password' : 'password123',
            'name' : 'Test Name',
        }

        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_short_password(self):
        payload = {
            'email' : 'test@example.com',
            'password' : 'ps',
            'name' : 'Test Name',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_users(self):
        """
        Test generating token for valid credentials
        """

        user_details = {
            'name' : 'Test Name',
            'email' : 'test@example.com',
            'password' : 'testpass123',
        }
        create_user(**user_details)

        payload = {
            'email' : user_details['email'],
            'password' : user_details['password'],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """ Expecting to fail the test when there is a bad credential for token generation"""
        user_details = {
            'name' : 'Test Name',
            'email' : 'test@example.com',
            'password' : 'testpass123',
        }
        create_user(**user_details)
        payload = {
            'email' : user_details['email'],
            'password' : 'badpass',
        }

        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_empty_password(self):
        create_user(email='test@example.com', password='testpass123')
        payload = {
            'email' : 'test@example.com',
            'password' : ''
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateUserApiTests(TestCase):
    """Test Api requests that require authentication"""
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test Name',
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile when everything is correct"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email' : self.user.email,
            'name' : self.user.name,
        })

    def test_post_not_allowed_for_me(self):
        """Test that POST is not allowed for me endpoint"""
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_updating_profile(self):

        payload = {
            'name' : 'Updated Name',
            'password' : 'newPass1234',
        }

        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)






