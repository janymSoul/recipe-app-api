"""Tests for recipe APIs"""
import tempfile
import os

from PIL import Image
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')

def image_upload_url(recipe_id):
    """Create and return an image upload URL."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title' : 'Sample recipe title',
        'time_minutes' : 5,
        'price' : Decimal('5.20'),
        'description' : 'Sample description',
        'link' : 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def detail_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args = [recipe_id])

def create_user(**params):
    """Create new user"""
    return get_user_model().objects.create_user(**params)
class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authorized API requests"""

    def setUp(self):
        self.client = APIClient()

        self.user = create_user(email='user@example.com',password='testpass123')
        self.client.force_authenticate(self.user)


    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user"""
        other_user = create_user(email='other@example.com', password='password123',)
        create_recipe(user=self.user)
        create_recipe(user=other_user)
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title' : 'Sample recipe',
            'time_minutes' : 30,
            'price' : Decimal('5.8'),
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link = original_link,
        )

        payload = {'title' : 'New recipe detail'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)

    def test_full_update(self):
        """Test full update recipe"""
        recipe = create_recipe(
            user = self.user,
            title = 'Sample recipe title',
            link = 'https://example.com/recipe.pdf',
            description = 'Sample recipe description',
        )

        payload = {
            'title' : 'New recipe title',
            'description' : 'New description',
            'link' : 'https://example.com/new-recipe.pdf',
            'time_minutes' : 10,
            'price' : Decimal('10.1'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user"""
        new_user = create_user(email='user2@example.com', password='user2123')
        recipe=create_recipe(user=self.user)

        payload = {
            'user' : new_user.id
        }

        res = self.client.patch(payload)
        recipe.refresh_from_db()

        self.assertEqual(recipe.user.id, self.user.id)

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title' : 'Thai Pawn Curry',
            'time_minutes' : 30,
            'price' : Decimal('5.5'),
            'tags' : [{'name' : 'Thai'}, {'name' : 'Dinner'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test when user tries to create recipe with existing tag"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title' : 'Pongal',
            'time_minutes' : 30,
            'price' : Decimal('0.5'),
            'tags' : [{'name' : 'Indian'}, {'name' : 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            )
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test adding tag on update"""
        recipe = create_recipe(user=self.user)
        payload = {
            'tags' : [{'name' : 'lunch'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        payload = {
            'title' : 'Sample Title',
            'time_minutes' : 10,
            'price' : Decimal('2.3'),
            'description' : 'sample description',
            'ingredients' : [
                {'name' : 'salt'},
                {'name' : 'pepper'},
                {'name' : 'meat'},
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.all().filter(user=self.user).order_by('-title')
        self.assertEqual(len(recipes), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        ingredients = recipe.ingredients.all()
        for ingredient in payload['ingredients']:
            exists = ingredients.filter(name=ingredient['name'], user=self.user)
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a recipe with existing ingredient"""
        ingredient1 = Ingredient.objects.create(name='cucumber', user=self.user)
        payload = {
            'title' : 'Sample Title',
            'time_minutes' : 10,
            'price' : Decimal('2.3'),
            'description' : 'sample description',
            'ingredients' : [
                {'name' : 'cucumber'},
                {'name' : 'pepper'},
                {'name' : 'meat'},
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.all().filter(user=self.user)
        self.assertEqual(len(recipes), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        self.assertIn(ingredient1, recipe.ingredients.all())
        ingredients = recipe.ingredients.all()
        for ingredient in payload['ingredients']:
            exists = ingredients.filter(name=ingredient['name'], user=self.user)
            self.assertTrue(exists)

    def test_update_recipe_with_new_ingredient(self):
        """Test adding an ingredient to existing recipe"""
        recipe = create_recipe(user = self.user)
        payload = {
            'ingredients' : [
                {'name' : 'pepper'},
                {'name' : 'salt'},
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        new_ingredient = Ingredient.objects.get(user=self.user, name='pepper')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_filter_by_tags(self):
        """Test filtering recipes by tags"""
        r1 = create_recipe(user=self.user, title='Thai Curry')
        r2 = create_recipe(user=self.user, title='Aubergine')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='Fish')

        params = {'tags' : f'{tag1.id}, {tag2.id}'}
        res = self.client.get(RECIPES_URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering the recipes by ingredients"""
        r1 = create_recipe(user=self.user, title='Thai Curry')
        r2 = create_recipe(user=self.user, title='Aubergine')
        r3 = create_recipe(user=self.user, title='Fish')
        ingredient1 = Ingredient.objects.create(user=self.user, name='salt')
        ingredient2 = Ingredient.objects.create(user=self.user, name='pepper')
        r1.ingredients.add(ingredient1)
        r2.ingredients.add(ingredient2)

        params = {
            'ingredients' : f'{ingredient1.id},{ingredient2.id}'
        }

        res = self.client.get(RECIPES_URL, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (15,15))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
                'image' : image_file
            }
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)

        payload = {'image' : 'string'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

