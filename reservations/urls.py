"""
URL configuration for the Reservations app.

Routes:
    POST /api/reservations/                → Create reservation
    GET  /api/reservations/                → List reservations
    GET  /api/reservations/{id}/           → Reservation details
    PUT  /api/reservations/{id}/release/   → Release locker
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'reservations'

router = DefaultRouter()
router.register('', views.ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
]
