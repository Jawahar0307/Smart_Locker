"""
Root URL configuration for Smart Storage Locker Management System.

Routes:
    /                → Redirects to Swagger UI
    /admin/          → Django admin panel
    /api/            → API root (lists all endpoints)
    /api/auth/       → Authentication endpoints (register, login, token refresh)
    /api/lockers/    → Locker management endpoints
    /api/reservations/ → Reservation management endpoints
    /api/docs/       → Swagger UI (API documentation)
    /api/health/     → Health check endpoint
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request: Request) -> Response:
    """Health check endpoint for monitoring and load balancers."""
    return Response({
        'status': 'healthy',
        'service': 'Smart Storage Locker Management System',
        'version': '1.0.0',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request: Request) -> Response:
    """API root endpoint listing all available routes."""
    return Response({
        'service': 'Smart Storage Locker Management System',
        'version': '1.0.0',
        'endpoints': {
            'docs': request.build_absolute_uri('/api/docs/'),
            'health': request.build_absolute_uri('/api/health/'),
            'auth': {
                'register': request.build_absolute_uri('/api/auth/register/'),
                'login': request.build_absolute_uri('/api/auth/login/'),
                'refresh': request.build_absolute_uri('/api/auth/refresh/'),
                'profile': request.build_absolute_uri('/api/auth/profile/'),
                'change_password': request.build_absolute_uri('/api/auth/change-password/'),
            },
            'lockers': {
                'list_create': request.build_absolute_uri('/api/lockers/'),
                'available': request.build_absolute_uri('/api/lockers/available/'),
            },
            'reservations': {
                'list_create': request.build_absolute_uri('/api/reservations/'),
            },
        },
    })


def root_redirect(request):
    """Redirect root URL to Swagger documentation."""
    return redirect('/api/docs/')


urlpatterns = [
    # Root redirect to docs
    path('', root_redirect, name='root'),

    # Django Admin
    path('admin/', admin.site.urls),

    # API Root
    path('api/', api_root, name='api-root'),

    # API Routes
    path('api/auth/', include('users.urls')),
    path('api/lockers/', include('lockers.urls')),
    path('api/reservations/', include('reservations.urls')),

    # Health Check
    path('api/health/', health_check, name='health-check'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]
