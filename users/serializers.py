"""
Serializers for user registration, login, and profile management.
"""

import logging
from typing import Any

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Accepts name, email, password, and optional role.
    Creates a new user with hashed password.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Minimum 8 characters.',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Must match the password field.',
    )
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        default=User.Role.USER,
        help_text='Role: admin or user.',
    )

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'password_confirm', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value: str) -> str:
        """Normalize and validate email uniqueness."""
        return value.lower().strip()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Ensure password and password_confirm match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create a new user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Generate a username from email
        email = validated_data['email']
        username = email.split('@')[0]

        # Ensure username uniqueness
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            password=password,
            **validated_data,
        )

        logger.info(
            'New user registered: %s (role=%s)',
            user.email,
            user.role,
            extra={'user_id': user.id, 'role': user.role},
        )

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Validates credentials and returns JWT tokens.
    """

    email = serializers.EmailField(help_text='Registered email address.')
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Authenticate user and generate JWT tokens."""
        email = attrs['email'].lower().strip()
        password = attrs['password']

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password,
        )

        if user is None:
            logger.warning(
                'Failed login attempt for email: %s',
                email,
                extra={'email': email, 'action': 'login_failed'},
            )
            raise serializers.ValidationError(
                'Invalid email or password.'
            )

        if not user.is_active:
            logger.warning(
                'Login attempt for inactive user: %s',
                email,
                extra={'email': email, 'action': 'login_inactive'},
            )
            raise serializers.ValidationError(
                'User account is disabled.'
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        logger.info(
            'User logged in: %s',
            user.email,
            extra={'user_id': user.id, 'action': 'login_success'},
        )

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
        }


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for user profile data.
    """

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'created_at', 'updated_at']
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )

    def validate_old_password(self, value: str) -> str:
        """Verify the current password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
