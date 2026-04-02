"""
Admin configuration for Locker model.
"""

from django.contrib import admin

from .models import Locker


@admin.register(Locker)
class LockerAdmin(admin.ModelAdmin):
    """
    Admin interface for managing lockers.


    Provides filtering by status and location, search by locker number,
    and a clear display of all relevant locker information.
    """

    list_display = ('locker_number', 'location', 'size', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'size', 'location')
    search_fields = ('locker_number', 'location')
    ordering = ('locker_number',)
    readonly_fields = ('created_at', 'updated_at')

    list_per_page = 25
