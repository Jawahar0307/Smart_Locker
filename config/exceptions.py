"""
Custom exception handler for the Smart Storage Locker Management System.

Provides structured error responses and logs all exceptions for
Kibana/ELK monitoring.
"""

import logging
from typing import Any, Optional

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Optional[Response]:
    """
    Custom exception handler that provides structured error responses
    and logs exceptions for monitoring.

    Args:
        exc: The exception that was raised.
        context: Additional context including the view and request.

    Returns:
        A Response object with structured error data, or None.
    """
    response = exception_handler(exc, context)

    view_name = (
        context.get('view').__class__.__name__
        if context.get('view')
        else 'Unknown'
    )

    if response is not None:
        error_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': _get_error_message(response),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data},
            },
        }
        response.data = error_data

        logger.warning(
            'API error in %s: %s (status=%d)',
            view_name,
            _get_error_message(response),
            response.status_code,
            extra={
                'status_code': response.status_code,
                'view': view_name,
                'error_type': exc.__class__.__name__,
            },
        )
    else:
        # Unhandled exception — log as critical
        logger.exception(
            'Unhandled exception in %s: %s',
            view_name,
            str(exc),
            extra={
                'view': view_name,
                'error_type': exc.__class__.__name__,
            },
        )
        response = Response(
            {
                'success': False,
                'error': {
                    'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'An unexpected error occurred.',
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_message(response: Response) -> str:
    """Extract a human-readable error message from a DRF response."""
    data = response.data
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        # Return first error message found
        for key, value in data.items():
            if isinstance(value, list) and value:
                return f"{key}: {value[0]}"
            elif isinstance(value, str):
                return f"{key}: {value}"
    elif isinstance(data, list) and data:
        return str(data[0])
    return 'An error occurred.'


class LockerNotAvailableError(APIException):
    """Raised when a locker is not available for reservation."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'This locker is not available for reservation.'
    default_code = 'locker_not_available'


class LockerAlreadyReservedError(APIException):
    """Raised when a user tries to reserve a locker that is already occupied."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'This locker is already reserved by another user.'
    default_code = 'locker_already_reserved'


class ReservationNotActiveError(APIException):
    """Raised when trying to release a reservation that is not active."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'This reservation is not active and cannot be released.'
    default_code = 'reservation_not_active'
