"""
Unit tests for the Lockers app.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User

from .models import Locker


class LockerModelTest(TestCase):
    """Tests for the Locker model."""

    def test_create_locker(self) -> None:
        """Test creating a locker with default values."""
        locker = Locker.objects.create(
            locker_number='A-101',
            location='Building A, Floor 1',
        )
        self.assertEqual(locker.locker_number, 'A-101')
        self.assertEqual(locker.status, Locker.Status.AVAILABLE)
        self.assertEqual(locker.size, Locker.Size.MEDIUM)
        self.assertTrue(locker.is_available)

    def test_locker_str(self) -> None:
        """Test locker string representation."""
        locker = Locker.objects.create(
            locker_number='B-202',
            location='Building B',
        )
        self.assertIn('B-202', str(locker))


class LockerViewSetTest(TestCase):
    """Tests for locker API endpoints."""

    def setUp(self) -> None:
        self.client = APIClient()

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            name='Admin',
            role=User.Role.ADMIN,
        )

        # Create regular user
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123',
            name='Regular User',
        )

        # Create a locker
        self.locker = Locker.objects.create(
            locker_number='A-101',
            location='Building A',
            size=Locker.Size.MEDIUM,
        )

    def test_admin_create_locker(self) -> None:
        """Test admin can create a locker."""
        self.client.force_authenticate(user=self.admin)
        data = {
            'locker_number': 'C-301',
            'location': 'Building C',
            'size': 'large',
        }
        response = self.client.post(
            reverse('lockers:locker-list'), data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_create_locker(self) -> None:
        """Test regular user cannot create a locker."""
        self.client.force_authenticate(user=self.user)
        data = {
            'locker_number': 'D-401',
            'location': 'Building D',
        }
        response = self.client.post(
            reverse('lockers:locker-list'), data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_lockers(self) -> None:
        """Test authenticated user can list lockers."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('lockers:locker-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_deactivate_locker(self) -> None:
        """Test admin can deactivate a locker."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse('lockers:locker-detail', args=[self.locker.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.locker.refresh_from_db()
        self.assertEqual(self.locker.status, Locker.Status.DEACTIVATED)
