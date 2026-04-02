"""
Serializers for locker management.
"""

from rest_framework import serializers

from .models import Locker


class LockerSerializer(serializers.ModelSerializer):
    """
    Full serializer for locker CRUD operations.

    Used by admins for creating and updating lockers,
    and by all authenticated users for viewing locker details.
    """

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )
    size_display = serializers.CharField(
        source='get_size_display',
        read_only=True,
    )

    class Meta:
        model = Locker
        fields = [
            'id',
            'locker_number',
            'location',
            'size',
            'size_display',
            'status',
            'status_display',
            'is_available',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_available', 'created_at', 'updated_at']

    def validate_locker_number(self, value: str) -> str:
        """Normalize locker number to uppercase."""
        return value.upper().strip()


class LockerAvailableSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the available lockers list.

    Used for the Redis-cached available lockers endpoint.
    Returns only essential fields for faster serialization.
    """

    class Meta:
        model = Locker
        fields = [
            'id',
            'locker_number',
            'location',
            'size',
            'status',
        ]
