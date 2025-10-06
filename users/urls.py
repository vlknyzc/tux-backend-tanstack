from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
    debug_auth_status
)
from .management_views import UserManagementViewSet, WorkspaceUserManagementViewSet
from .invitation_views import (
    InvitationViewSet,
    InvitationValidateView,
    RegisterViaInvitationView,
    InvitationStatsView
)
from . import email_views

# Create router for user management endpoints
router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user-management')
router.register(r'workspace-users', WorkspaceUserManagementViewSet,
                basename='workspace-user-management')
router.register(r'invitations', InvitationViewSet, basename='invitation')

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),

    # JWT authentication endpoints
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('logout/', LogoutView.as_view()),
    
    # Debug endpoint
    path('debug/auth-status/', debug_auth_status, name='debug-auth-status'),
    
    # Invitation-specific endpoints (non-REST)
    path('invitations/<uuid:token>/validate/', InvitationValidateView.as_view(), name='invitation-validate'),
    path('register-via-invitation/', RegisterViaInvitationView.as_view(), name='register-via-invitation'),
    path('invitations/stats/', InvitationStatsView.as_view(), name='invitation-stats'),
    
    # Email API endpoints
    path('email/test/', email_views.send_test_email, name='send-test-email'),
    path('email/send/', email_views.send_custom_email, name='send-custom-email'),
]
