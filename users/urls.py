"""
URL configuration for the Users app.

Routes:
    POST /api/auth/register/         → Register new user
    POST /api/auth/login/            → Login (get JWT)
    POST /api/auth/refresh/          → Refresh JWT token
    GET  /api/auth/profile/          → Get user profile
    PUT  /api/auth/change-password/  → Change password
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]
