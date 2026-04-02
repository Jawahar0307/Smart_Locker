"""
Reservation model for the Smart Storage Locker Management System.

Tracks locker reservations with status management and
automatic timestamp tracking.
"""

from django.conf import settings
from django.db import models


class Reservation(models.Model):
    """
    Represents a locker reservation by a user.

    Tracks the lifecycle of a reservation from creation (active)
    through release or expiration.

    Attributes:
        user: The user who made the reservation.
        locker: The locker that was reserved.
        status: Current reservation status — active, released, or expired.
        reserved_at: Timestamp when the reservation was created.
        released_at: Timestamp when the locker was released (nullable).
        created_at: Record creation timestamp.
        updated_at: Record last update timestamp.
    """

    class Status(models.TextChoices):
        """Reservation lifecycle statuses."""
        ACTIVE = 'active', 'Active'
        RELEASED = 'released', 'Released'
        EXPIRED = 'expired', 'Expired'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        help_text='The user who made this reservation.',
    )
    locker = models.ForeignKey(
        'lockers.Locker',
        on_delete=models.CASCADE,
        related_name='reservations',
        help_text='The locker that is reserved.',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text='Current status of the reservation.',
    )
    reserved_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the reservation was made.',
    )
    released_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the locker was released.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reservations'
        ordering = ['-reserved_at']
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'
        # Ensure a locker can only have one active reservation
        constraints = [
            models.UniqueConstraint(
                fields=['locker'],
                condition=models.Q(status='active'),
                name='unique_active_reservation_per_locker',
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Reservation #{self.id}: "
            f"User {self.user.name} → Locker {self.locker.locker_number} "
            f"({self.get_status_display()})"
        )

    @property
    def is_active(self) -> bool:
        """Check if the reservation is currently active."""
        return self.status == self.Status.ACTIVE
