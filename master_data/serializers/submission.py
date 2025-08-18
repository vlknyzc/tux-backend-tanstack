from rest_framework import serializers
from django.db import transaction
from .. import models
from typing import Optional


# =============================================================================
# WRITE SERIALIZERS (for creating/updating data)
# =============================================================================

class SubmissionWithStringsSerializer(serializers.ModelSerializer):
    """
    Serializer for creating submissions with optional initial_strings.
    Implements Option 3 (Extended Submission Creation) from the design document.
    """

    # Import the StringWithDetailsSerializer locally to avoid circular import
    initial_strings = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
        help_text="Initial strings to create with the submission"
    )
    strings = serializers.SerializerMethodField(read_only=True)
    rule = serializers.PrimaryKeyRelatedField(
        queryset=models.Rule.objects.all(),
        help_text="The naming rule to apply for this submission"
    )
    starting_field = serializers.PrimaryKeyRelatedField(
        queryset=models.Field.objects.all(),
        help_text="The field to start the naming sequence from"
    )
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = models.Submission
        fields = [
            'id', 'name', 'slug', 'description', 'rule', 'starting_field',
            'status', 'workspace', 'created', 'last_updated', 'created_by',
            'initial_strings', 'strings'
        ]
        read_only_fields = ['id', 'slug',
                            'workspace', 'created', 'last_updated']

    def get_rule(self, obj):
        """Get rule info."""
        return {
            'id': obj.rule.id,
            'name': obj.rule.name,
            'platform': obj.rule.platform.id
        }

    def get_starting_field(self, obj):
        """Get starting field info."""
        return {
            'id': obj.starting_field.id,
            'name': obj.starting_field.name,
            'field_level': obj.starting_field.field_level
        }

    def get_created_by(self, obj):
        """Get created by info."""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            }
        return None

    def get_strings(self, obj):
        """Get associated strings if requested."""
        # Only include strings in response if they exist
        if hasattr(obj, '_created_strings'):
            # Import here to avoid circular import
            from .string import StringWithDetailsReadSerializer
            return StringWithDetailsReadSerializer(obj._created_strings, many=True).data
        return []

    @transaction.atomic
    def create(self, validated_data):
        """Create submission with optional initial strings atomically."""
        initial_strings_data = validated_data.pop('initial_strings', [])

        # Create submission using the parent class (which will call perform_create)
        submission = super().create(validated_data)

        # Create initial strings if provided
        created_strings = []
        if initial_strings_data:
            # Import here to avoid circular import
            from .string import StringWithDetailsSerializer

            for string_data in initial_strings_data:
                string_data['submission'] = submission.id

                string_serializer = StringWithDetailsSerializer(
                    data=string_data,
                    context=self.context
                )
                string_serializer.is_valid(raise_exception=True)
                string = string_serializer.save()
                created_strings.append(string)

        # Attach created strings for response
        submission._created_strings = created_strings

        return submission


# =============================================================================
# READ SERIALIZERS (for displaying/retrieving data)
# =============================================================================

class SubmissionWithStringsReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for submissions that returns expanded field objects.
    Used for GET requests to provide rich field information.
    """

    strings = serializers.SerializerMethodField()
    rule = serializers.SerializerMethodField()
    starting_field = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = models.Submission
        fields = [
            'id', 'name', 'slug', 'description', 'rule', 'starting_field',
            'status', 'workspace', 'created', 'last_updated', 'created_by', 'strings'
        ]
        read_only_fields = ['id', 'name', 'slug', 'description', 'rule', 'starting_field',
                            'status', 'workspace', 'created', 'last_updated', 'created_by', 'strings']

    def get_rule(self, obj):
        """Get rule info."""
        return {
            'id': obj.rule.id,
            'name': obj.rule.name,
            'platform': obj.rule.platform.id
        }

    def get_starting_field(self, obj):
        """Get starting field info."""
        return {
            'id': obj.starting_field.id,
            'name': obj.starting_field.name,
            'field_level': obj.starting_field.field_level
        }

    def get_created_by(self, obj):
        """Get created by info."""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'name': f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            }
        return None

    def get_strings(self, obj):
        """Get associated strings with expanded field information."""
        strings = obj.submission_strings.all()
        # Import here to avoid circular import
        from .string import StringWithDetailsReadSerializer
        return StringWithDetailsReadSerializer(strings, many=True).data
