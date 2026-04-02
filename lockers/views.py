"""
Views for locker management.

Endpoints:
    POST   /api/lockers/              → Create locker (Admin only)
    GET    /api/lockers/              → List all lockers
    GET    /api/lockers/{id}/         → Get locker details
    PUT    /api/lockers/{id}/         → Update locker (Admin only)
    DELETE /api/lockers/{id}/         → Deactivate locker (Admin only)
    GET    /api/lockers/available/    → List available lockers (Redis cached)
"""

import json
import logging

from django.core.cache import cache
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin

from .models import Locker
from .serializers import LockerAvailableSerializer, LockerSerializer

logger = logging.getLogger(__name__)

# Redis cache key and TTL
AVAILABLE_LOCKERS_CACHE_KEY = 'available_lockers'
AVAILABLE_LOCKERS_CACHE_TTL = 60  # seconds


@extend_schema_view(
    list=extend_schema(tags=['Lockers'], summary='List all lockers'),
    create=extend_schema(tags=['Lockers'], summary='Create a new locker (Admin)'),
    retrieve=extend_schema(tags=['Lockers'], summary='Get locker details'),
    update=extend_schema(tags=['Lockers'], summary='Update a locker (Admin)'),
    partial_update=extend_schema(tags=['Lockers'], summary='Partially update a locker (Admin)'),
    destroy=extend_schema(tags=['Lockers'], summary='Deactivate a locker (Admin)'),
)
class LockerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for locker management.

    - Admin users can create, update, and deactivate lockers.
    - Authenticated users can list and view locker details.
    - DELETE soft-deactivates the locker instead of hard-deleting.
    """

    queryset = Locker.objects.all()
    serializer_class = LockerSerializer

    def get_permissions(self):
        """
        Apply role-based permissions:
        - create, update, partial_update, destroy → Admin only
        - list, retrieve → Any authenticated user
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new locker (Admin only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        locker = serializer.save()

        logger.info(
            'Locker created: %s by admin %s',
            locker.locker_number,
            request.user.email,
            extra={
                'locker_id': locker.id,
                'locker_number': locker.locker_number,
                'admin_id': request.user.id,
                'action': 'locker_created',
            },
        )

        return Response(
            {
                'success': True,
                'message': f'Locker {locker.locker_number} created successfully.',
                'data': serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a locker (Admin only)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        locker = serializer.save()

        logger.info(
            'Locker updated: %s by admin %s',
            locker.locker_number,
            request.user.email,
            extra={
                'locker_id': locker.id,
                'admin_id': request.user.id,
                'action': 'locker_updated',
            },
        )

        return Response(
            {
                'success': True,
                'message': f'Locker {locker.locker_number} updated successfully.',
                'data': serializer.data,
            },
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """
        Soft-deactivate a locker (Admin only).

        Instead of deleting the record, sets the status to 'deactivated'.
        """
        locker = self.get_object()
        locker.status = Locker.Status.DEACTIVATED
        locker.save(update_fields=['status', 'updated_at'])

        logger.info(
            'Locker deactivated: %s by admin %s',
            locker.locker_number,
            request.user.email,
            extra={
                'locker_id': locker.id,
                'admin_id': request.user.id,
                'action': 'locker_deactivated',
            },
        )

        return Response(
            {
                'success': True,
                'message': f'Locker {locker.locker_number} has been deactivated.',
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=['Lockers'],
    summary='List available lockers (Redis cached)',
    description=(
        'Returns the list of currently available lockers. '
        'Results are cached in Redis for 60 seconds to improve performance.'
    ),
)
class AvailableLockersView(APIView):
    """
    List available lockers with Redis caching.

    Caching strategy:
        1. Check Redis for cached data.
        2. If found → return cached data (cache hit).
        3. If not found → query DB, serialize, store in Redis with 60s TTL, return.
        4. On reservation/release → cache expires naturally (no manual invalidation).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return list of available lockers, using Redis cache."""

        # Step 1: Check Redis cache
        cached_data = cache.get(AVAILABLE_LOCKERS_CACHE_KEY)

        if cached_data is not None:
            logger.debug(
                'Available lockers cache HIT',
                extra={'action': 'cache_hit', 'key': AVAILABLE_LOCKERS_CACHE_KEY},
            )
            return Response(
                {
                    'success': True,
                    'source': 'cache',
                    'count': len(cached_data),
                    'data': cached_data,
                },
            )

        # Step 2: Cache miss — query database
        logger.debug(
            'Available lockers cache MISS — querying database',
            extra={'action': 'cache_miss', 'key': AVAILABLE_LOCKERS_CACHE_KEY},
        )

        available_lockers = Locker.objects.filter(
            status=Locker.Status.AVAILABLE
        )
        serializer = LockerAvailableSerializer(available_lockers, many=True)
        locker_data = serializer.data

        # Step 3: Store in Redis with TTL
        cache.set(
            AVAILABLE_LOCKERS_CACHE_KEY,
            locker_data,
            timeout=AVAILABLE_LOCKERS_CACHE_TTL,
        )

        logger.info(
            'Available lockers cached: %d lockers (TTL=%ds)',
            len(locker_data),
            AVAILABLE_LOCKERS_CACHE_TTL,
            extra={
                'action': 'cache_set',
                'count': len(locker_data),
                'ttl': AVAILABLE_LOCKERS_CACHE_TTL,
            },
        )

        return Response(
            {
                'success': True,
                'source': 'database',
                'count': len(locker_data),
                'data': locker_data,
            },
        )
