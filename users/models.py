"""
User models for the Smart Storage Locker Management System.

Defines a custom User model with role-based access control supporting
Admin and regular User roles.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access control.

    Extends Django's AbstractUser to add role field and
    timestamp tracking. Supports two roles:
        - admin: Can create lockers, manage users
        - user: Can reserve and use lockers

    Attributes:
        name: Full name of the user.
        email: Unique email address (used for login).
        role: User role — 'admin' or 'user'.
        created_at: Timestamp when the user was created.
        updated_at: Timestamp of the last update.
    """

    class Role(models.TextChoices):
        """Enumeration of available user roles."""
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'

    name = models.CharField(
        max_length=255,
        help_text='Full name of the user.',
    )
    email = models.EmailField(
        unique=True,
        help_text='Unique email address used for authentication.',
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
        help_text='Role of the user — admin or user.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"

    @property
    def is_admin_user(self) -> bool:
        """Check if the user has admin role."""
        return self.role == self.Role.ADMIN
