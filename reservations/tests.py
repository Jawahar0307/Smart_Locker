"""
Unit tests for the Reservations app.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from lockers.models import Locker
from users.models import User

from .models import Reservation


class ReservationModelTest(TestCase):
    """Tests for the Reservation model."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User',
        )
        self.locker = Locker.objects.create(
            locker_number='A-101',
            location='Building A',
        )

    def test_create_reservation(self) -> None:
        """Test creating a reservation."""
        reservation = Reservation.objects.create(
            user=self.user,
            locker=self.locker,
        )
        self.assertEqual(reservation.status, Reservation.Status.ACTIVE)
        self.assertTrue(reservation.is_active)
        self.assertIsNone(reservation.released_at)


class ReservationViewSetTest(TestCase):
    """Tests for reservation API endpoints."""

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123',
            name='Test User',
        )

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            name='Admin User',
            role=User.Role.ADMIN,
        )

        self.locker = Locker.objects.create(
            locker_number='A-101',
            location='Building A',
            status=Locker.Status.AVAILABLE,
        )

    def test_create_reservation(self) -> None:
        """Test user can create a reservation."""
        self.client.force_authenticate(user=self.user)
        data = {'locker_id': self.locker.id}
        response = self.client.post(
            reverse('reservations:reservation-list'), data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify locker is now occupied
        self.locker.refresh_from_db()
        self.assertEqual(self.locker.status, Locker.Status.OCCUPIED)

    def test_cannot_reserve_occupied_locker(self) -> None:
        """Test reservation fails for occupied locker."""
        # First reservation
        self.client.force_authenticate(user=self.user)
        self.client.post(
            reverse('reservations:reservation-list'),
            {'locker_id': self.locker.id},
            format='json',
        )

        # Second user tries same locker
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpass123',
            name='Other User',
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.post(
            reverse('reservations:reservation-list'),
            {'locker_id': self.locker.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_release_reservation(self) -> None:
        """Test user can release their reservation."""
        self.client.force_authenticate(user=self.user)

        # Create reservation
        response = self.client.post(
            reverse('reservations:reservation-list'),
            {'locker_id': self.locker.id},
            format='json',
        )
        reservation_id = response.data['data']['id']

        # Release it
        response = self.client.put(
            reverse('reservations:reservation-release', args=[reservation_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify locker is available again
        self.locker.refresh_from_db()
        self.assertEqual(self.locker.status, Locker.Status.AVAILABLE)

    def test_user_sees_only_own_reservations(self) -> None:
        """Test user can only see their own reservations."""
        # Create reservation for user
        Reservation.objects.create(user=self.user, locker=self.locker)

        # Another user
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpass123',
            name='Other User',
        )

        self.client.force_authenticate(user=other_user)
        response = self.client.get(reverse('reservations:reservation-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_admin_sees_all_reservations(self) -> None:
        """Test admin can see all reservations."""
        Reservation.objects.create(user=self.user, locker=self.locker)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('reservations:reservation-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
