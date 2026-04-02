"""
Admin configuration for Reservation model.
"""

from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    Admin interface for managing reservations.

    Provides comprehensive display of reservation data including
    user, locker, status, and timestamps with filtering and search.
    """

    list_display = (
        'id',
        'user',
        'locker',
        'status',
        'reserved_at',
        'released_at',
    )
    list_filter = ('status', 'reserved_at', 'released_at')
    search_fields = (
        'user__name',
        'user__email',
        'locker__locker_number',
    )
    ordering = ('-reserved_at',)
    readonly_fields = ('reserved_at', 'released_at', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'locker')

    list_per_page = 25
