from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from master_data.models import Workspace
from .models import WorkspaceUser, Invitation

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


# Invitation Serializers

class InvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invitations"""
    
    class Meta:
        model = Invitation
        fields = ['email', 'workspace', 'role', 'expires_at']
        extra_kwargs = {
            'expires_at': {'required': False}
        }
    
    def validate_email(self, value):
        """Validate that email doesn't already have an account"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists"
            )
        return value.lower()
    
    def validate(self, attrs):
        """Additional validation"""
        # Check if there's already a pending invitation for this email
        email = attrs.get('email')
        workspace = attrs.get('workspace')
        
        if email and workspace:
            existing_invitation = Invitation.objects.filter(
                email=email,
                workspace=workspace,
                status='pending'
            ).first()
            
            if existing_invitation and existing_invitation.is_valid:
                raise serializers.ValidationError(
                    "A pending invitation already exists for this email and workspace"
                )
        
        return attrs
    
    def create(self, validated_data):
        """Create invitation with invitor from request"""
        request = self.context.get('request')
        validated_data['invitor'] = request.user
        return super().create(validated_data)


class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for invitation details"""
    invitor_name = serializers.CharField(source='invitor.get_full_name', read_only=True)
    invitor_email = serializers.CharField(source='invitor.email', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'token', 'email', 'role', 'status',
            'created_at', 'updated_at', 'expires_at', 'used_at',
            'invitor_name', 'invitor_email', 'workspace', 'workspace_name',
            'is_valid', 'is_expired'
        ]
        read_only_fields = [
            'id', 'token', 'created_at', 'updated_at', 'used_at',
            'invitor_name', 'invitor_email', 'workspace_name',
            'is_valid', 'is_expired'
        ]


class InvitationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for invitation lists"""
    invitor_name = serializers.CharField(source='invitor.get_full_name', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'token', 'email', 'role', 'status',
            'created_at', 'expires_at', 'invitor_name', 'workspace_name',
            'is_valid', 'days_until_expiry'
        ]
    
    def get_days_until_expiry(self, obj):
        """Calculate days until expiry"""
        if obj.status != 'pending':
            return None
        
        delta = obj.expires_at - timezone.now()
        if delta.days < 0:
            return 0
        return delta.days


class InvitationValidationSerializer(serializers.Serializer):
    """Serializer for invitation validation response"""
    valid = serializers.BooleanField()
    status = serializers.CharField()
    email = serializers.EmailField()
    invitor_name = serializers.CharField()
    workspace_name = serializers.CharField(allow_null=True)
    role = serializers.CharField()
    expires_at = serializers.DateTimeField()
    message = serializers.CharField()


class RegisterViaInvitationSerializer(serializers.Serializer):
    """Serializer for user registration via invitation"""
    token = serializers.UUIDField()
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate invitation token and password confirmation"""
        token = attrs.get('token')
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        # Validate password confirmation
        if password != password_confirm:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate invitation token
        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token")
        
        if not invitation.is_valid:
            if invitation.is_expired:
                raise serializers.ValidationError("Invitation has expired")
            elif invitation.status == 'used':
                raise serializers.ValidationError("Invitation has already been used")
            elif invitation.status == 'revoked':
                raise serializers.ValidationError("Invitation has been revoked")
            else:
                raise serializers.ValidationError("Invitation is not valid")
        
        # Check if user already exists with this email
        if User.objects.filter(email=invitation.email).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        attrs['invitation'] = invitation
        return attrs
    
    def create(self, validated_data):
        """Create user from invitation"""
        invitation = validated_data.pop('invitation')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create user with invitation email
        user = User.objects.create_user(
            email=invitation.email,
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=True
        )
        
        # Mark invitation as used
        invitation.mark_as_used(user)
        
        # Create workspace relationship if invitation has workspace
        if invitation.workspace:
            WorkspaceUser.objects.create(
                user=user,
                workspace=invitation.workspace,
                role=invitation.role,
                is_active=True
            )
        
        return user


class InvitationResendSerializer(serializers.Serializer):
    """Serializer for resending invitations"""
    message = serializers.CharField(default="Invitation resent successfully")
    new_expires_at = serializers.DateTimeField()
