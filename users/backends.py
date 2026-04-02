"""
Custom authentication backend to support email-based login.
"""

from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email instead of username.
    """

    def authenticate(
        self,
        request: Optional[HttpRequest] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.

        Args:
            request: The HTTP request.
            email: The user's email address.
            password: The user's password.

        Returns:
            The authenticated User object, or None.
        """
        if email is None or password is None:
            return None

        try:
            user = User.objects.get(email=email.lower().strip())
        except User.DoesNotExist:
            # Run the default password hasher to reduce timing attacks
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
