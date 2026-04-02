"""
URL configuration for the Lockers app.

Routes:
    POST   /api/lockers/              → Create locker (Admin)
    GET    /api/lockers/              → List all lockers
    GET    /api/lockers/{id}/         → Locker details
    PUT    /api/lockers/{id}/         → Update locker (Admin)
    DELETE /api/lockers/{id}/         → Deactivate locker (Admin)
    GET    /api/lockers/available/    → Available lockers (Redis cached)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'lockers'

router = DefaultRouter()
router.register('', views.LockerViewSet, basename='locker')

urlpatterns = [
    # Available lockers (must be before router to avoid conflict with {id})
    path('available/', views.AvailableLockersView.as_view(), name='available-lockers'),

    # Locker CRUD
    path('', include(router.urls)),
]
