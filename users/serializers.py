from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WorkspaceUser

User = get_user_model()


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


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with workspace information"""
    workspace_assignments = WorkspaceUserSerializer(
        source='workspaceuser_set', many=True, read_only=True
    )
    accessible_workspaces_count = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'is_staff', 'is_superuser', 'last_login',
            'workspace_assignments', 'accessible_workspaces_count'
        ]
        read_only_fields = ['id', 'last_login']

    def get_accessible_workspaces_count(self, obj):
        """Get count of accessible workspaces"""
        if obj.is_superuser:
            from master_data.models import Workspace
            return Workspace.objects.count()
        return obj.workspaces.filter(workspaceuser__is_active=True).count()


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
            from master_data.models import Workspace
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
