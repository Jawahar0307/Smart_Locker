"""
Views for user authentication and profile management.

Endpoints:
    POST /api/auth/register/    → Register a new user
    POST /api/auth/login/       → Login and get JWT tokens
    POST /api/auth/refresh/     → Refresh JWT token
    GET  /api/auth/profile/     → Get current user profile
    PUT  /api/auth/change-password/ → Change password
"""

import logging

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Authentication'],
    summary='Register a new user',
    description='Create a new user account with name, email, password, and role.',
)
class RegisterView(generics.CreateAPIView):
    """
    Register a new user.

    Creates a new user account and returns the user data.
    No authentication required.
    """

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                'success': True,
                'message': 'User registered successfully.',
                'data': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=['Authentication'],
    summary='Login',
    description='Authenticate with email and password to receive JWT tokens.',
)
class LoginView(APIView):
    """
    Login and get JWT tokens.

    Accepts email and password, returns access and refresh tokens
    along with user profile data.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                'success': True,
                'message': 'Login successful.',
                'data': serializer.validated_data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=['Authentication'],
    summary='Get user profile',
    description='Retrieve the authenticated user\'s profile information.',
)
class ProfileView(generics.RetrieveAPIView):
    """
    Get the current authenticated user's profile.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=['Authentication'],
    summary='Change password',
    description='Change the authenticated user\'s password.',
)
class ChangePasswordView(APIView):
    """
    Change the current user's password.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def put(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        logger.info(
            'Password changed for user: %s',
            request.user.email,
            extra={'user_id': request.user.id, 'action': 'password_changed'},
        )

        return Response(
            {
                'success': True,
                'message': 'Password changed successfully.',
            },
            status=status.HTTP_200_OK,
        )
