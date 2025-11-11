"""
Serializers for Project models.
"""

from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from .. import models


# =============================================================================
# USER SERIALIZERS
# =============================================================================

class UserBasicSerializer(serializers.Serializer):
    """Basic user info for nested representations."""
    id = serializers.IntegerField()
    name = serializers.CharField(source='get_full_name')
    email = serializers.EmailField()
    avatar = serializers.CharField(required=False, allow_null=True)


# =============================================================================
# PLATFORM SERIALIZERS
# =============================================================================

class PlatformBasicSerializer(serializers.Serializer):
    """Basic platform info for nested representations."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    platform_type = serializers.CharField()


# =============================================================================
# PROJECT MEMBER SERIALIZERS
# =============================================================================

class ProjectMemberReadSerializer(serializers.ModelSerializer):
    """Serializer for reading project members."""
    user = UserBasicSerializer()

    class Meta:
        model = models.ProjectMember
        fields = ['id', 'user', 'role', 'created']


class ProjectMemberWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating project members."""
    user_id = serializers.IntegerField()

    class Meta:
        model = models.ProjectMember
        fields = ['user_id', 'role']


# =============================================================================
# PROJECT ACTIVITY SERIALIZERS
# =============================================================================

class ProjectActivitySerializer(serializers.ModelSerializer):
    """Serializer for project activities."""
    user_id = serializers.IntegerField(source='user.id', allow_null=True)
    user_name = serializers.CharField(source='user.get_full_name', allow_null=True)
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = models.ProjectActivity
        fields = [
            'id', 'project_id', 'type', 'description',
            'user_id', 'user_name', 'user_avatar',
            'metadata', 'created'
        ]

    def get_user_avatar(self, obj):
        """Get user avatar (placeholder for now)."""
        return None


# =============================================================================
# APPROVAL HISTORY SERIALIZERS
# =============================================================================

class ApprovalHistorySerializer(serializers.ModelSerializer):
    """Serializer for approval history."""
    user_id = serializers.IntegerField(source='user.id', allow_null=True)
    user_name = serializers.CharField(source='user.get_full_name', allow_null=True)

    class Meta:
        model = models.ApprovalHistory
        fields = [
            'id', 'action', 'comment', 'timestamp',
            'user_id', 'user_name'
        ]


# =============================================================================
# PROJECT SERIALIZERS
# =============================================================================

class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for listing projects (minimal data)."""
    owner_name = serializers.CharField(source='owner.get_full_name')
    platforms = PlatformBasicSerializer(many=True, read_only=True)
    team_members = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = models.Project
        fields = [
            'id', 'name', 'slug', 'description', 'status',
            'start_date', 'end_date', 'owner_id', 'owner_name',
            'workspace', 'platforms', 'team_members',
            'stats', 'created', 'last_updated', 'approval_status'
        ]

    def get_team_members(self, obj):
        """Get team members for this project."""
        members = obj.team_members.all().select_related('user')
        return ProjectMemberReadSerializer(members, many=True).data

    def get_stats(self, obj):
        """Get project statistics."""
        total_strings = models.String.objects.filter(project=obj).count()
        platforms_count = obj.platforms.count()
        team_members_count = obj.team_members.count()

        # Get last activity
        last_activity = obj.activities.order_by('-created').first()
        last_activity_date = last_activity.created if last_activity else None

        return {
            'total_strings': total_strings,
            'platforms_count': platforms_count,
            'team_members_count': team_members_count,
            'last_activity': last_activity_date
        }


class ProjectDetailSerializer(ProjectListSerializer):
    """Serializer for project detail with full data."""
    strings = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()
    approval_history = serializers.SerializerMethodField()

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + ['strings', 'activities', 'approval_history']

    def get_strings(self, obj):
        """Get strings for this project (using StringReadSerializer)."""
        from .project_string import StringReadSerializer
        # Use for_workspace to explicitly filter by the project's workspace
        # This ensures we get strings for the correct workspace
        strings = models.String.objects.for_workspace(obj.workspace_id).filter(
            project=obj
        ).select_related(
            'platform', 'entity', 'rule', 'created_by'
        ).prefetch_related('details')
        return StringReadSerializer(strings, many=True).data

    def get_activities(self, obj):
        """Get activities for this project."""
        activities = obj.activities.all().select_related('user').order_by('-created')
        return ProjectActivitySerializer(activities, many=True).data

    def get_approval_history(self, obj):
        """Get approval history for this project."""
        history = models.ApprovalHistory.objects.filter(
            project=obj
        ).order_by('-timestamp')[:10]  # Last 10 entries
        return ApprovalHistorySerializer(history, many=True).data


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects."""
    platforms = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=models.Platform.objects.all(),
        required=False
    )
    team_members = ProjectMemberWriteSerializer(many=True, required=False)

    class Meta:
        model = models.Project
        fields = [
            'name', 'description', 'status', 'start_date', 'end_date',
            'workspace', 'platforms', 'team_members'
        ]

    def validate(self, attrs):
        """Validate project data."""
        # Validate end_date >= start_date
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date must be after start date")

        # Validate at least one team member has role 'owner'
        team_members = attrs.get('team_members', [])
        if team_members:
            has_owner = any(member['role'] == 'owner' for member in team_members)
            if not has_owner:
                raise serializers.ValidationError(
                    "At least one team member must have role 'owner'"
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create project with related data."""
        platforms = validated_data.pop('platforms', [])
        team_members_data = validated_data.pop('team_members', [])

        # Get current user from context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['owner'] = request.user

        # Create project
        project = models.Project.objects.create(**validated_data)

        # Assign platforms
        if platforms:
            project.platforms.set(platforms)

        # Create team members
        for member_data in team_members_data:
            from users.models import UserAccount
            user = UserAccount.objects.get(id=member_data['user_id'])
            models.ProjectMember.objects.create(
                project=project,
                user=user,
                role=member_data['role']
            )

            # Create activity
            models.ProjectActivity.objects.create(
                project=project,
                user=request.user if request and hasattr(request, 'user') else None,
                type='member_assigned',
                description=f"assigned {user.get_full_name()} as {member_data['role']}"
            )

        # Create project created activity
        models.ProjectActivity.objects.create(
            project=project,
            user=request.user if request and hasattr(request, 'user') else None,
            type='project_created',
            description="created the project"
        )

        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects."""
    platforms = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=models.Platform.objects.all(),
        required=False
    )
    team_members = ProjectMemberWriteSerializer(many=True, required=False)

    class Meta:
        model = models.Project
        fields = [
            'name', 'description', 'status', 'start_date', 'end_date',
            'platforms', 'team_members'
        ]

    def validate(self, attrs):
        """Validate project update data."""
        # Validate end_date >= start_date
        start_date = attrs.get('start_date', self.instance.start_date)
        end_date = attrs.get('end_date', self.instance.end_date)
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date must be after start date")

        # Validate approval status
        if self.instance.approval_status == 'approved':
            raise serializers.ValidationError(
                "Cannot update approved project without unlock"
            )

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update project with related data."""
        platforms = validated_data.pop('platforms', None)
        team_members_data = validated_data.pop('team_members', None)

        request = self.context.get('request')

        # Track status change
        old_status = instance.status

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update platforms if provided
        if platforms is not None:
            instance.platforms.set(platforms)

        # Update team members if provided
        if team_members_data is not None:
            # Clear existing members
            instance.team_members.all().delete()

            # Create new members
            for member_data in team_members_data:
                from users.models import UserAccount
                user = UserAccount.objects.get(id=member_data['user_id'])
                models.ProjectMember.objects.create(
                    project=instance,
                    user=user,
                    role=member_data['role']
                )

        # Create activity for status change
        if 'status' in validated_data and old_status != instance.status:
            models.ProjectActivity.objects.create(
                project=instance,
                user=request.user if request and hasattr(request, 'user') else None,
                type='status_changed',
                description=f"changed status from {old_status} to {instance.status}"
            )

        # Create project updated activity
        models.ProjectActivity.objects.create(
            project=instance,
            user=request.user if request and hasattr(request, 'user') else None,
            type='project_updated',
            description="updated the project"
        )

        return instance


# =============================================================================
# APPROVAL ACTION SERIALIZERS
# =============================================================================

class SubmitForApprovalSerializer(serializers.Serializer):
    """Serializer for submitting for approval."""
    comment = serializers.CharField(required=False, allow_blank=True)


class ApproveSerializer(serializers.Serializer):
    """Serializer for approving."""
    comment = serializers.CharField(required=False, allow_blank=True)


class RejectSerializer(serializers.Serializer):
    """Serializer for rejecting."""
    reason = serializers.CharField(required=True)
