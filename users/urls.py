from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView
)
from .management_views import UserManagementViewSet, WorkspaceUserManagementViewSet

# Create router for user management endpoints
router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user-management')
router.register(r'workspace-users', WorkspaceUserManagementViewSet,
                basename='workspace-user-management')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),

    # JWT authentication endpoints
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('logout/', LogoutView.as_view()),
]
