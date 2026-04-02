"""
Lockers app configuration.
"""

from django.apps import AppConfig


class LockersConfig(AppConfig):
    """Configuration for the Lockers application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lockers'
    verbose_name = 'Locker Management'
