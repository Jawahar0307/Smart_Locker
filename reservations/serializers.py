"""
Serializers for reservation management.
"""

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from config.exceptions import (
    LockerAlreadyReservedError,
    LockerNotAvailableError,
    ReservationNotActiveError,
)
from lockers.models import Locker
from lockers.serializers import LockerSerializer
from users.serializers import UserSerializer

from .models import Reservation

logger = logging.getLogger(__name__)


class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and reading reservations.

    On creation:
        - Validates the locker is available.
        - Uses select_for_update() to prevent race conditions.
        - Marks the locker as occupied.
    """

    user = UserSerializer(read_only=True)
    locker_details = LockerSerializer(source='locker', read_only=True)
    locker_id = serializers.PrimaryKeyRelatedField(
        queryset=Locker.objects.all(),
        source='locker',
        write_only=True,
        help_text='ID of the locker to reserve.',
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )

    class Meta:
        model = Reservation
        fields = [
            'id',
            'user',
            'locker_id',
            'locker_details',
            'status',
            'status_display',
            'reserved_at',
            'released_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'status', 'reserved_at',
            'released_at', 'created_at', 'updated_at',
        ]

    def validate_locker_id(self, locker: Locker) -> Locker:
        """Validate that the selected locker is available."""
        if locker.status == Locker.Status.DEACTIVATED:
            raise serializers.ValidationError(
                'This locker has been deactivated.'
            )
        if locker.status == Locker.Status.MAINTENANCE:
            raise serializers.ValidationError(
                'This locker is under maintenance.'
            )
        return locker

    def create(self, validated_data: dict[str, Any]) -> Reservation:
        """
        Create a reservation with concurrency control.

        Uses select_for_update() to lock the locker row during the
        transaction, preventing double-booking.
        """
        user = self.context['request'].user
        locker = validated_data['locker']

        with transaction.atomic():
            # Lock the locker row to prevent race conditions
            locked_locker = (
                Locker.objects
                .select_for_update()
                .get(pk=locker.pk)
            )

            if not locked_locker.is_available:
                raise LockerNotAvailableError()

            # Check if user already has an active reservation for this locker
            existing = Reservation.objects.filter(
                user=user,
                locker=locked_locker,
                status=Reservation.Status.ACTIVE,
            ).exists()

            if existing:
                raise LockerAlreadyReservedError(
                    detail='You already have an active reservation for this locker.'
                )

            # Mark locker as occupied
            locked_locker.status = Locker.Status.OCCUPIED
            locked_locker.save(update_fields=['status', 'updated_at'])

            # Create the reservation
            reservation = Reservation.objects.create(
                user=user,
                locker=locked_locker,
                status=Reservation.Status.ACTIVE,
            )

        logger.info(
            'Reservation created: User %s → Locker %s',
            user.email,
            locked_locker.locker_number,
            extra={
                'user_id': user.id,
                'locker_id': locked_locker.id,
                'reservation_id': reservation.id,
                'action': 'reservation_created',
            },
        )

        return reservation


class ReleaseReservationSerializer(serializers.Serializer):
    """
    Serializer for releasing a reservation (giving back the locker).

    Validates the reservation is active and handles the release
    within a database transaction.
    """

    def update(self, instance: Reservation, validated_data: dict) -> Reservation:
        """
        Release the reservation and mark the locker as available.

        Args:
            instance: The active Reservation to release.

        Returns:
            The updated Reservation with released status.
        """
        if not instance.is_active:
            raise ReservationNotActiveError()

        with transaction.atomic():
            # Lock the locker
            locker = (
                Locker.objects
                .select_for_update()
                .get(pk=instance.locker.pk)
            )

            # Release the reservation
            instance.status = Reservation.Status.RELEASED
            instance.released_at = timezone.now()
            instance.save(update_fields=['status', 'released_at', 'updated_at'])

            # Mark the locker as available
            locker.status = Locker.Status.AVAILABLE
            locker.save(update_fields=['status', 'updated_at'])

        logger.info(
            'Reservation released: User %s → Locker %s',
            instance.user.email,
            locker.locker_number,
            extra={
                'user_id': instance.user.id,
                'locker_id': locker.id,
                'reservation_id': instance.id,
                'action': 'reservation_released',
            },
        )

        return instance
