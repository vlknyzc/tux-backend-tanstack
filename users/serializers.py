from rest_framework import serializers
from django.contrib.auth import get_user_model
from master_data.models import Workspace
from .models import WorkspaceUser

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'last_login',]
        read_only_fields = ['id']


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for list views"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    workspace_count = serializers.SerializerMethodField()
    primary_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'is_staff', 'is_superuser', 'last_login',
            'workspace_count', 'primary_role'
        ]

    def get_workspace_count(self, obj):
        """Get count of active workspace assignments"""
        if obj.is_superuser:
            return Workspace.objects.count()
        return obj.workspaces.filter(workspaceuser__is_active=True).count()

    def get_primary_role(self, obj):
        """Get the user's primary role (superuser, admin, user, etc.)"""
        if obj.is_superuser:
            return 'superuser'

        # Get the most privileged role across workspaces
        roles = obj.workspaceuser_set.filter(
            is_active=True).values_list('role', flat=True)
        if 'admin' in roles:
            return 'admin'
        elif 'user' in roles:
            return 'user'
        elif 'viewer' in roles:
            return 'viewer'
        return 'no_access'


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'is_active', 'is_staff', 'is_superuser'
        ]

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser'
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with workspace relationships"""
    accessible_workspaces = serializers.SerializerMethodField()
    accessible_workspaces_count = serializers.SerializerMethodField()
    current_workspace = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'is_active', 'is_superuser',
            'accessible_workspaces', 'accessible_workspaces_count',
            'current_workspace'
        ]
        read_only_fields = ['id']

    def get_accessible_workspaces(self, obj):
        """Get list of workspaces the user has access to"""
        try:
            if hasattr(obj, 'get_accessible_workspaces'):
                workspaces = obj.get_accessible_workspaces()
                return [
                    {
                        'id': ws.id,
                        'name': ws.name,
                        'slug': ws.slug
                    }
                    for ws in workspaces
                ]
            return []
        except Exception:
            return []

    def get_accessible_workspaces_count(self, obj):
        """Get count of accessible workspaces"""
        try:
            if hasattr(obj, 'get_accessible_workspaces'):
                return len(obj.get_accessible_workspaces())
            return 0
        except Exception:
            return 0

    def get_current_workspace(self, obj):
        """Get current workspace context if available"""
        request = self.context.get('request')
        if request and hasattr(request, 'workspace'):
            workspace = request.workspace
            if workspace:
                return {
                    'id': workspace.id,
                    'name': workspace.name,
                    'slug': workspace.slug
                }
        return None


class WorkspaceUserSerializer(serializers.ModelSerializer):
    """Serializer for WorkspaceUser relationships"""
    workspace_name = serializers.CharField(
        source='workspace.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)

    class Meta:
        model = WorkspaceUser
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'workspace', 'workspace_name',
            'role', 'is_active', 'created', 'updated'
        ]
        read_only_fields = ['id', 'created', 'updated']


class WorkspaceUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating WorkspaceUser relationships"""

    class Meta:
        model = WorkspaceUser
        fields = ['user', 'workspace', 'role', 'is_active']


class UserAuthorizationSummarySerializer(serializers.Serializer):
    """Serializer for user authorization summary"""
    user_id = serializers.IntegerField()
    email = serializers.CharField()
    full_name = serializers.CharField()
    is_superuser = serializers.BooleanField()
    is_active = serializers.BooleanField()
    workspace_authorizations = serializers.ListField(
        child=serializers.DictField(), allow_empty=True
    )
    total_workspaces = serializers.IntegerField()
    active_assignments = serializers.IntegerField()


class LogoutResponseSerializer(serializers.Serializer):
    """Serializer for logout response"""
    message = serializers.CharField(default="Successfully logged out")
    status = serializers.CharField(default="success")
