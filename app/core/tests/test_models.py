"""
Tests for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test models"""
    def test_create_user_model_with_email_successful(self):
        """ Test creating a user with a successful email """
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_model_with_email_normalize(self):
        """Test creating a user with normalized email"""
        sample = [
            ['test@EXAMPLE.com', 'test@example.com'],
            ['tesT1@ExamplE.com', 'tesT1@example.com'],
            ['Test2@example.com', 'Test2@example.com'],
        ]

        for email, correct in sample:
            user = get_user_model().objects.create_user(email=email, password='samplepass123')
            self.assertEqual(user.email, correct)

    def test_new_user_without_email_raise_error(self):
        """Raising Error when email is empty"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        superuser = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )

        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.isStaff)


