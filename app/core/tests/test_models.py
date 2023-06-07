"""
Tests for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from decimal import Decimal
from unittest.mock import patch

from core import models

def create_user(email='user@example.com', password='userpass123'):
    """Create and return new user"""
    return get_user_model().objects.create_user(email=email, password=password)



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
        self.assertTrue(superuser.is_staff)

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample Recipe Name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description.',
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating ingredient is successful."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Ingredient',
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path"""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
