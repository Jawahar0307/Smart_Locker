"""
Locker model for the Smart Storage Locker Management System.

Defines locker entities with status tracking, size categorization,
and location management.
"""

from django.db import models


class Locker(models.Model):
    """
    Represents a physical storage locker in the system.

    Each locker has a unique number, a location, a size category,
    and a status that tracks its current availability.

    Attributes:
        locker_number: Unique identifier for the locker (e.g., "A-101").
        location: Physical location/zone of the locker (e.g., "Building A, Floor 1").
        size: Size category — small, medium, or large.
        status: Current status — available, occupied, maintenance, or deactivated.
        created_at: Timestamp when the locker was added to the system.
        updated_at: Timestamp of the last status change or update.
    """

    class Size(models.TextChoices):
        """Available locker size categories."""
        SMALL = 'small', 'Small'
        MEDIUM = 'medium', 'Medium'
        LARGE = 'large', 'Large'

    class Status(models.TextChoices):
        """Locker availability statuses."""
        AVAILABLE = 'available', 'Available'
        OCCUPIED = 'occupied', 'Occupied'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
        DEACTIVATED = 'deactivated', 'Deactivated'

    locker_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text='Unique locker identifier (e.g., "A-101").',
    )
    location = models.CharField(
        max_length=255,
        help_text='Physical location of the locker.',
    )
    size = models.CharField(
        max_length=10,
        choices=Size.choices,
        default=Size.MEDIUM,
        help_text='Size category of the locker.',
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
        help_text='Current status of the locker.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lockers'
        ordering = ['locker_number']
        verbose_name = 'Locker'
        verbose_name_plural = 'Lockers'

    def __str__(self) -> str:
        return f"Locker {self.locker_number} ({self.location}) — {self.get_status_display()}"

    @property
    def is_available(self) -> bool:
        """Check if the locker is available for reservation."""
        return self.status == self.Status.AVAILABLE
