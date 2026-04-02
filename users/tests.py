"""
Unit tests for the Users app.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import User


class UserModelTest(TestCase):
    """Tests for the User model."""

    def test_create_user(self) -> None:
        """Test creating a regular user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User',
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertEqual(user.role, User.Role.USER)
        self.assertFalse(user.is_admin_user)

    def test_create_admin_user(self) -> None:
        """Test creating an admin user."""
        user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123',
            name='Admin User',
            role=User.Role.ADMIN,
        )
        self.assertTrue(user.is_admin_user)


class RegisterViewTest(TestCase):
    """Tests for user registration endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse('users:register')

    def test_register_success(self) -> None:
        """Test successful user registration."""
        data = {
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_password_mismatch(self) -> None:
        """Test registration fails with mismatched passwords."""
        data = {
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'differentpass',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_email(self) -> None:
        """Test registration fails with duplicate email."""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123',
            name='Existing User',
        )
        data = {
            'name': 'New User',
            'email': 'existing@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)


class LoginViewTest(TestCase):
    """Tests for user login endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse('users:login')
        self.user = User.objects.create_user(
            username='logintest',
            email='login@example.com',
            password='testpass123',
            name='Login Test User',
        )

    def test_login_success(self) -> None:
        """Test successful login returns JWT tokens."""
        data = {
            'email': 'login@example.com',
            'password': 'testpass123',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access', response.data['data']['tokens'])
        self.assertIn('refresh', response.data['data']['tokens'])

    def test_login_invalid_credentials(self) -> None:
        """Test login fails with wrong password."""
        data = {
            'email': 'login@example.com',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
