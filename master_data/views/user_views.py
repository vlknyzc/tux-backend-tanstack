from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from .. import serializers
from django.conf import settings


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.UserCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return serializers.UserUpdateSerializer
        elif self.action == 'retrieve':
            return serializers.UserDetailSerializer
        return serializers.UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny() if settings.DEBUG else permissions.IsAuthenticated()]
