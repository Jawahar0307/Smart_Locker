"""
Views for reservation management.

Endpoints:
    POST /api/reservations/                → Create reservation
    GET  /api/reservations/                → List reservations (user: own / admin: all)
    GET  /api/reservations/{id}/           → Get reservation details
    PUT  /api/reservations/{id}/release/   → Release locker (cancel reservation)
"""

import logging

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from users.permissions import IsOwnerOrAdmin

from .models import Reservation
from .serializers import ReleaseReservationSerializer, ReservationSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=['Reservations'],
        summary='List reservations',
        description='Users see their own reservations. Admins see all.',
    ),
    create=extend_schema(tags=['Reservations'], summary='Create a reservation'),
    retrieve=extend_schema(tags=['Reservations'], summary='Get reservation details'),
)
class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing locker reservations.

    - Users can create reservations and view their own.
    - Admins can view all reservations.
    - Release action cancels an active reservation and frees the locker.
    """

    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'head', 'options']

    def get_queryset(self):
        """
        Filter reservations based on user role:
        - Admin: can see all reservations.
        - User: can only see their own reservations.
        """
        user = self.request.user

        if user.role == 'admin':
            return Reservation.objects.select_related('user', 'locker').all()

        return Reservation.objects.select_related('user', 'locker').filter(
            user=user
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a new reservation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = serializer.save()

        return Response(
            {
                'success': True,
                'message': (
                    f'Locker {reservation.locker.locker_number} '
                    f'reserved successfully.'
                ),
                'data': ReservationSerializer(reservation).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=['Reservations'],
        summary='Release a locker',
        description='Cancel an active reservation and make the locker available again.',
        request=None,
    )
    @action(
        detail=True,
        methods=['put'],
        url_path='release',
        url_name='release',
    )
    def release(self, request: Request, pk=None) -> Response:
        """
        Release a locker reservation.

        Marks the reservation as released and sets the locker
        status back to available.
        """
        reservation = self.get_object()

        # Check ownership (user can only release their own, admin can release any)
        if (
            request.user.role != 'admin'
            and reservation.user != request.user
        ):
            return Response(
                {
                    'success': False,
                    'error': {
                        'message': 'You can only release your own reservations.',
                    },
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReleaseReservationSerializer(data={})
        serializer.is_valid(raise_exception=True)
        updated_reservation = serializer.update(reservation, {})

        return Response(
            {
                'success': True,
                'message': (
                    f'Locker {updated_reservation.locker.locker_number} '
                    f'released successfully.'
                ),
                'data': ReservationSerializer(updated_reservation).data,
            },
            status=status.HTTP_200_OK,
        )
