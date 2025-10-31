"""
Serializers for ProjectString models.
"""

from rest_framework import serializers
from django.db import transaction
from .. import models


# =============================================================================
# PROJECT STRING DETAIL SERIALIZERS
# =============================================================================

class ProjectStringDetailNestedSerializer(serializers.ModelSerializer):
    """Serializer for project string details when nested in string creation/updates."""

    # Add dimension metadata
    dimension_name = serializers.CharField(source='dimension.name', read_only=True)
    dimension_type = serializers.CharField(source='dimension.dimension_type', read_only=True)
    dimension_value_display = serializers.SerializerMethodField()
    dimension_value_label = serializers.SerializerMethodField()

    class Meta:
        model = models.ProjectStringDetail
        fields = [
            'id', 'dimension', 'dimension_name', 'dimension_type',
            'dimension_value_id', 'dimension_value', 'dimension_value_freetext',
            'dimension_value_display', 'dimension_value_label',
            'is_inherited'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'dimension_value_id': {'source': 'dimension_value.id', 'read_only': True}
        }

    def get_dimension_value_display(self, obj):
        """Get display value for the dimension value."""
        if obj.dimension_value:
            return obj.dimension_value.value
        return obj.dimension_value_freetext

    def get_dimension_value_label(self, obj):
        """Get label for the dimension value."""
        if obj.dimension_value:
            return obj.dimension_value.label
        return obj.dimension_value_freetext


class ProjectStringDetailWriteSerializer(serializers.Serializer):
    """Serializer for writing project string details."""
    dimension = serializers.IntegerField()
    dimension_value = serializers.IntegerField(required=False, allow_null=True)
    dimension_value_freetext = serializers.CharField(required=False, allow_null=True, allow_blank=True)

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


# =============================================================================
# PROJECT STRING READ SERIALIZERS
# =============================================================================

class ProjectStringReadSerializer(serializers.ModelSerializer):
    """Serializer for reading project strings."""
    project_name = serializers.CharField(source='project.name', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)
    field_level = serializers.IntegerField(source='field.field_level', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    details = ProjectStringDetailNestedSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProjectString
        fields = [
            'id', 'project_id', 'project_name', 'platform_id', 'platform_name',
            'field_id', 'field_name', 'field_level', 'rule_id', 'rule_name',
            'value', 'string_uuid', 'parent_uuid',
            'created_by', 'created_by_name', 'created', 'last_updated',
            'details'
        ]

    def get_created_by_name(self, obj):
        """Get creator name."""
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None


class ProjectStringExpandedSerializer(ProjectStringReadSerializer):
    """Serializer for expanded project string with hierarchy and suggestions."""
    hierarchy_path = serializers.SerializerMethodField()
    can_have_children = serializers.SerializerMethodField()
    suggested_child_field = serializers.SerializerMethodField()

    class Meta(ProjectStringReadSerializer.Meta):
        fields = ProjectStringReadSerializer.Meta.fields + [
            'hierarchy_path', 'can_have_children', 'suggested_child_field'
        ]

    def get_hierarchy_path(self, obj):
        """Get the full hierarchy path for this string."""
        return obj.get_hierarchy_path()

    def get_can_have_children(self, obj):
        """Check if string can have children."""
        return obj.can_have_children()

    def get_suggested_child_field(self, obj):
        """Get suggested next field for child strings."""
        next_field = obj.suggest_child_field()
        if next_field:
            return {
                'id': next_field.id,
                'name': next_field.name,
                'field_level': next_field.field_level
            }
        return None


# =============================================================================
# PROJECT STRING WRITE SERIALIZERS
# =============================================================================

class ProjectStringWriteSerializer(serializers.Serializer):
    """Serializer for writing individual project strings (used in bulk create)."""
    field = serializers.IntegerField()
    string_uuid = serializers.UUIDField()
    parent_uuid = serializers.UUIDField(required=False, allow_null=True)
    value = serializers.CharField(max_length=500)
    details = ProjectStringDetailWriteSerializer(many=True)


class BulkProjectStringCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating project strings."""
    rule = serializers.IntegerField()
    starting_field = serializers.IntegerField()
    strings = ProjectStringWriteSerializer(many=True)

    def validate(self, attrs):
        """Validate bulk string creation data."""
        rule_id = attrs['rule']
        starting_field_id = attrs['starting_field']
        strings_data = attrs['strings']

        # Validate rule exists
        try:
            rule = models.Rule.objects.get(id=rule_id)
        except models.Rule.DoesNotExist:
            raise serializers.ValidationError(f"Rule with id {rule_id} does not exist")

        # Validate starting field belongs to rule's platform
        try:
            starting_field = models.Field.objects.get(id=starting_field_id)
            if starting_field.platform != rule.platform:
                raise serializers.ValidationError(
                    "Starting field must belong to the rule's platform"
                )
        except models.Field.DoesNotExist:
            raise serializers.ValidationError(
                f"Field with id {starting_field_id} does not exist"
            )

        # Validate all fields belong to rule's platform
        field_ids = {s['field'] for s in strings_data}
        fields = models.Field.objects.filter(id__in=field_ids)
        for field in fields:
            if field.platform != rule.platform:
                raise serializers.ValidationError(
                    f"Field {field.name} does not belong to the rule's platform"
                )

        # Validate string UUIDs are unique
        string_uuids = [s['string_uuid'] for s in strings_data]
        if len(string_uuids) != len(set(string_uuids)):
            raise serializers.ValidationError("Duplicate string UUIDs found")

        # Validate parent UUIDs reference strings in same platform (will be checked at creation)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create project strings in bulk."""
        project = self.context['project']
        platform = self.context['platform']
        rule_id = validated_data['rule']
        strings_data = validated_data['strings']

        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None

        rule = models.Rule.objects.get(id=rule_id)

        created_strings = []
        string_uuid_map = {}  # Map UUIDs to created string instances

        # Sort strings by field level to ensure parents are created first
        strings_by_level = {}
        for string_data in strings_data:
            field = models.Field.objects.get(id=string_data['field'])
            level = field.field_level
            if level not in strings_by_level:
                strings_by_level[level] = []
            strings_by_level[level].append(string_data)

        # Create strings level by level
        for level in sorted(strings_by_level.keys()):
            for string_data in strings_by_level[level]:
                field = models.Field.objects.get(id=string_data['field'])
                details_data = string_data.pop('details')

                # Get parent if parent_uuid is provided
                parent = None
                parent_uuid = string_data.get('parent_uuid')
                if parent_uuid:
                    # Check if parent was just created in this batch
                    if parent_uuid in string_uuid_map:
                        parent = string_uuid_map[parent_uuid]
                    else:
                        # Look for existing parent
                        try:
                            parent = models.ProjectString.objects.get(
                                string_uuid=parent_uuid,
                                platform=platform
                            )
                        except models.ProjectString.DoesNotExist:
                            raise serializers.ValidationError(
                                f"Parent string with UUID {parent_uuid} not found in platform {platform.name}"
                            )

                # Create string
                project_string = models.ProjectString.objects.create(
                    project=project,
                    platform=platform,
                    field=field,
                    rule=rule,
                    parent=parent,
                    string_uuid=string_data['string_uuid'],
                    parent_uuid=parent_uuid,
                    value=string_data['value'],
                    created_by=user,
                    workspace=project.workspace
                )

                # Store in map for parent lookups
                string_uuid_map[project_string.string_uuid] = project_string

                # Create string details
                for detail_data in details_data:
                    dimension = models.Dimension.objects.get(id=detail_data['dimension'])
                    dimension_value = None
                    dimension_value_freetext = None

                    if 'dimension_value' in detail_data and detail_data['dimension_value']:
                        dimension_value = models.DimensionValue.objects.get(
                            id=detail_data['dimension_value']
                        )
                    else:
                        dimension_value_freetext = detail_data.get('dimension_value_freetext')

                    # Check if inherited from parent
                    is_inherited = False
                    if parent:
                        # Check if parent has same dimension value
                        parent_detail = models.ProjectStringDetail.objects.filter(
                            string=parent,
                            dimension=dimension
                        ).first()

                        if parent_detail:
                            if dimension_value and parent_detail.dimension_value == dimension_value:
                                is_inherited = True
                            elif dimension_value_freetext and parent_detail.dimension_value_freetext == dimension_value_freetext:
                                is_inherited = True

                    models.ProjectStringDetail.objects.create(
                        string=project_string,
                        dimension=dimension,
                        dimension_value=dimension_value,
                        dimension_value_freetext=dimension_value_freetext,
                        is_inherited=is_inherited,
                        workspace=project.workspace
                    )

                created_strings.append(project_string)

        # Create project activity
        models.ProjectActivity.objects.create(
            project=project,
            user=user,
            type='strings_generated',
            description=f"generated {len(created_strings)} strings for {platform.name}",
            metadata={'string_count': len(created_strings), 'platform_id': platform.id}
        )

        return created_strings


class ProjectStringUpdateSerializer(serializers.Serializer):
    """Serializer for updating a project string."""
    value = serializers.CharField(max_length=500)
    details = ProjectStringDetailWriteSerializer(many=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update project string."""
        details_data = validated_data.pop('details')

        # Update value
        instance.value = validated_data['value']
        instance.save()

        # Clear existing details
        instance.details.all().delete()

        # Create new details
        for detail_data in details_data:
            dimension = models.Dimension.objects.get(id=detail_data['dimension'])
            dimension_value = None
            dimension_value_freetext = None

            if 'dimension_value' in detail_data and detail_data['dimension_value']:
                dimension_value = models.DimensionValue.objects.get(
                    id=detail_data['dimension_value']
                )
            else:
                dimension_value_freetext = detail_data.get('dimension_value_freetext')

            # Check if inherited from parent
            is_inherited = False
            if instance.parent:
                parent_detail = models.ProjectStringDetail.objects.filter(
                    string=instance.parent,
                    dimension=dimension
                ).first()

                if parent_detail:
                    if dimension_value and parent_detail.dimension_value == dimension_value:
                        is_inherited = True
                    elif dimension_value_freetext and parent_detail.dimension_value_freetext == dimension_value_freetext:
                        is_inherited = True

            models.ProjectStringDetail.objects.create(
                string=instance,
                dimension=dimension,
                dimension_value=dimension_value,
                dimension_value_freetext=dimension_value_freetext,
                is_inherited=is_inherited,
                workspace=instance.workspace
            )

        return instance


# =============================================================================
# LIST STRINGS SERIALIZERS
# =============================================================================

class ListProjectStringsSerializer(serializers.Serializer):
    """Serializer for list strings query parameters."""
    field = serializers.IntegerField(required=False)
    parent_field = serializers.IntegerField(required=False)
    parent_uuid = serializers.UUIDField(required=False)
    search = serializers.CharField(required=False)
    page = serializers.IntegerField(required=False, default=1)
    page_size = serializers.IntegerField(required=False, default=50)
