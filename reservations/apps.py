"""
Reservations app configuration.
"""

from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    """Configuration for the Reservations application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'
    verbose_name = 'Reservation Management'
