from rest_framework import serializers
from django.db import transaction
from .. import models
from .base import WorkspaceOwnedSerializer


# =============================================================================
# WRITE SERIALIZERS (for creating/updating data)
# =============================================================================

class StringDetailNestedSerializer(serializers.ModelSerializer):
    """Serializer for string details when nested in string creation/updates."""

    # Add these as SerializerMethodField to access dimension_value properties
    dimension_value_label = serializers.SerializerMethodField()
    dimension_value_value = serializers.SerializerMethodField()
    dimension_value_utm = serializers.SerializerMethodField()
    dimension_value_description = serializers.SerializerMethodField()

    class Meta:
        model = models.StringDetail
        fields = [
            'id', 'dimension', 'dimension_value', 'dimension_value_freetext',
            'dimension_value_label', 'dimension_value_value', 'dimension_value_utm', 'dimension_value_description'
        ]
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def get_dimension_value_label(self, obj):
        """Get the label of the dimension value."""
        if obj.dimension_value:
            return obj.dimension_value.label
        return None

    def get_dimension_value_value(self, obj):
        """Get the value of the dimension value."""
        if obj.dimension_value:
            return obj.dimension_value.value
        return None

    def get_dimension_value_utm(self, obj):
        """Get the UTM code of the dimension value."""
        if obj.dimension_value:
            return obj.dimension_value.utm
        return None

    def get_dimension_value_description(self, obj):
        """Get the description of the dimension value."""
        if obj.dimension_value:
            return obj.dimension_value.description
        return None

    def validate(self, attrs):
        """Validate that either dimension_value or dimension_value_freetext is provided."""
        dimension_value = attrs.get('dimension_value')
        dimension_value_freetext = attrs.get('dimension_value_freetext')

        if not dimension_value and not dimension_value_freetext:
            raise serializers.ValidationError(
                "Either dimension_value or dimension_value_freetext must be provided"
            )

        if dimension_value and dimension_value_freetext:
            raise serializers.ValidationError(
                "Cannot specify both dimension_value and dimension_value_freetext"
            )

        return attrs


class StringWithDetailsSerializer(WorkspaceOwnedSerializer):
    """
    Serializer for creating/updating strings with embedded details.
    Implements the details-first approach from the design document.
    """

    details = StringDetailNestedSerializer(many=True, source='string_details')
    entity = serializers.PrimaryKeyRelatedField(
        queryset=models.Entity.objects.all(),
        help_text="Entity this string belongs to"
    )
    submission = serializers.PrimaryKeyRelatedField(
        queryset=models.Submission.objects.none(),  # Filtered in __init__
        required=False,
        help_text="Submission that generated this string"
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=models.String.objects.none(),  # Filtered in __init__
        required=False,
        allow_null=True,
        help_text="Parent string for hierarchical relationships"
    )

    def __init__(self, *args, **kwargs):
        """Initialize serializer and filter querysets by workspace."""
        super().__init__(*args, **kwargs)

        # Get workspace from context
        workspace = self.context.get('workspace')
        if workspace:
            # Filter submission and parent querysets by workspace
            self.fields['submission'].queryset = models.Submission.objects.filter(
                workspace=workspace
            )
            self.fields['parent'].queryset = models.String.objects.filter(
                workspace=workspace
            )

    class Meta(WorkspaceOwnedSerializer.Meta):
        model = models.String
        fields = [
            'id', 'submission', 'entity', 'parent', 'string_uuid', 'parent_uuid',
            'is_auto_generated', 'generation_metadata', 'version', 'workspace',
            'created', 'last_updated', 'details', 'created_by', 'value'
        ]
        # Extend parent read_only_fields with additional auto-generated fields
        read_only_fields = WorkspaceOwnedSerializer.Meta.read_only_fields + ['version']
        extra_kwargs = {
            'string_uuid': {'required': False},
            'value': {'required': False}
        }

    def validate(self, attrs):
        """Validate and set workspace from submission context if not provided."""
        # If workspace is not provided but submission is, inherit workspace from submission
        if 'workspace' not in attrs and 'submission' in attrs:
            submission = attrs['submission']
            attrs['workspace'] = submission.workspace

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Create string with details atomically using details-first approach.
        String value is generated from details, not provided directly.
        """
        details_data = validated_data.pop('string_details', [])
        value = validated_data.pop('value', None)

        if not details_data:
            raise serializers.ValidationError("String details are required")

        # Ensure workspace is set before creating the string
        if 'workspace' not in validated_data:
            raise serializers.ValidationError("Workspace is required")

        # Create string
        validated_data['value'] = value
        string = models.String.objects.create(**validated_data)

        # Create details
        for detail_data in details_data:
            models.StringDetail.objects.create(
                string=string,
                workspace=string.workspace,
                **detail_data
            )

        # Generate correct value using existing service
        string.regenerate_value()

        return string

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update string with details atomically."""
        details_data = validated_data.pop('string_details', None)

        # Update string fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle details update if provided
        if details_data is not None:
            # Delete existing details
            instance.string_details.all().delete()

            # Create new details
            for detail_data in details_data:
                models.StringDetail.objects.create(
                    string=instance,
                    workspace=instance.workspace,
                    **detail_data
                )

            # Regenerate string value based on new details
            instance.regenerate_value()

        return instance


class StringDetailWriteSerializer(serializers.ModelSerializer):
    """
    Workspace-scoped string detail serializer for write operations.
    Updates to string details trigger automatic string regeneration.
    """

    class Meta:
        model = models.StringDetail
        fields = [
            'id', 'dimension', 'dimension_value', 'dimension_value_freetext',
            'string', 'created', 'last_updated'
        ]
        read_only_fields = ['id', 'created', 'last_updated']

    def update(self, instance, validated_data):
        """Update string detail and trigger string regeneration."""
        instance = super().update(instance, validated_data)

        # Trigger string regeneration
        instance.string.regenerate_value()

        return instance


# =============================================================================
# READ SERIALIZERS (for displaying/retrieving data)
# =============================================================================

class StringDetailExpandedSerializer(serializers.ModelSerializer):
    """Expanded serializer for string details with related object info."""

    dimension = serializers.SerializerMethodField()
    dimension_value = serializers.SerializerMethodField()
    effective_value = serializers.SerializerMethodField()

    class Meta:
        model = models.StringDetail
        fields = [
            'id', 'dimension', 'dimension_value', 'dimension_value_freetext',
            'effective_value'
        ]

    def get_dimension(self, obj):
        """Get dimension info."""
        return {
            'id': obj.dimension.id,
            'name': obj.dimension.name,
            'type': obj.dimension.type
        }

    def get_dimension_value(self, obj):
        """Get dimension value info if present."""
        if obj.dimension_value:
            return {
                'id': obj.dimension_value.id,
                'value': obj.dimension_value.value,
                'label': obj.dimension_value.label
            }
        return None

    def get_effective_value(self, obj):
        """Get the effective value."""
        return obj.get_effective_value()


class StringWithDetailsReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for strings that returns expanded field objects.
    Used for GET requests to provide rich field information.
    """

    details = StringDetailNestedSerializer(many=True, source='string_details')
    entity = serializers.SerializerMethodField()
    submission = serializers.SerializerMethodField()
    rule = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = models.String
        fields = [
            'id', 'submission', 'entity', 'rule', 'value', 'string_uuid',
            'parent', 'parent_uuid', 'is_auto_generated', 'generation_metadata',
            'version', 'workspace', 'created', 'last_updated', 'details', 'platform',
            'created_by'
        ]
        read_only_fields = ['id', 'submission', 'entity', 'rule', 'value', 'string_uuid',
                            'parent', 'parent_uuid', 'is_auto_generated', 'generation_metadata',
                            'version', 'workspace', 'created', 'last_updated', 'details', 'platform',
                            'created_by']

    def get_submission(self, obj):
        """Get submission info."""
        return {
            'id': obj.submission.id,
            'name': obj.submission.name
        }

    def get_entity(self, obj):
        """Get entity info."""
        return {
            'id': obj.entity.id,
            'name': obj.entity.name,
            'level': obj.entity.entity_level
        }

    def get_rule(self, obj):
        """Get rule info."""
        return {
            'id': obj.rule.id,
            'name': obj.rule.name
        }

    def get_platform(self, obj):
        """Get platform info."""
        return {
            'id': obj.entity.platform.id,
            'name': obj.entity.platform.name
        }

    def get_parent(self, obj):
        """Get parent string info."""
        if obj.parent:
            return {
                'id': obj.parent.id,
                'value': obj.parent.value,
                'string_uuid': str(obj.parent.string_uuid)
            }
        return None


class StringDetailReadSerializer(serializers.ModelSerializer):
    """
    Workspace-scoped string detail serializer for read operations.
    """

    dimension = serializers.SerializerMethodField()
    dimension_value = serializers.SerializerMethodField()
    string = serializers.SerializerMethodField()
    effective_value = serializers.SerializerMethodField()

    class Meta:
        model = models.StringDetail
        fields = [
            'id', 'dimension', 'dimension_value', 'dimension_value_freetext',
            'string', 'effective_value', 'created', 'last_updated'
        ]
        read_only_fields = ['id', 'created', 'last_updated']

    def get_dimension(self, obj):
        """Get dimension info."""
        return {
            'id': obj.dimension.id,
            'name': obj.dimension.name,
            'type': obj.dimension.type
        }

    def get_dimension_value(self, obj):
        """Get dimension value info if present."""
        if obj.dimension_value:
            return {
                'id': obj.dimension_value.id,
                'value': obj.dimension_value.value,
                'label': obj.dimension_value.label
            }
        return None

    def get_string(self, obj):
        """Get basic string info."""
        return {
            'id': obj.string.id,
            'value': obj.string.value,
            'version': obj.string.version
        }

    def get_effective_value(self, obj):
        """Get the effective value."""
        return obj.get_effective_value()
