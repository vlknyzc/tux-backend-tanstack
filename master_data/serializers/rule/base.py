"""
Write serializers for creating/updating Rule and RuleDetail models.

This module contains serializers responsible for creating and updating
rules and rule details with nested structures.
"""

import logging
from rest_framework import serializers
from typing import Optional
from django.core.exceptions import ObjectDoesNotExist
from ...models import Rule, RuleDetail, Entity, Platform, Workspace
from ..base import WorkspaceOwnedSerializer

logger = logging.getLogger(__name__)


class RuleDetailCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating rule details with validation."""

    class Meta:
        model = RuleDetail
        fields = [
            'entity',
            'dimension',
            'prefix',
            'suffix',
            'delimiter',
            'dimension_order',
            'is_required',
        ]
        extra_kwargs = {
            'rule': {'required': False, 'write_only': True}
        }

    def validate(self, attrs):
        """Enhanced validation for rule detail creation."""
        entity = attrs['entity']
        dimension = attrs['dimension']

        # Note: rule validation is handled at the RuleNestedSerializer level
        # since the rule doesn't exist yet when this serializer validates

        return attrs


class RuleCreateUpdateSerializer(WorkspaceOwnedSerializer):
    """Serializer for creating and updating rules."""

    workspace = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()

    class Meta(WorkspaceOwnedSerializer.Meta):
        model = Rule
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "is_default",
            "platform",
            "workspace",
            "workspace_name",
            "created_by",
            "created",
            "last_updated",
        ]

        # Extend parent read_only_fields with slug (auto-generated)
        read_only_fields = WorkspaceOwnedSerializer.Meta.read_only_fields + ['slug']

    def get_workspace(self, obj) -> int:
        return obj.workspace.id

    def get_workspace_name(self, obj) -> Optional[str]:
        return obj.workspace.name if obj.workspace else None


class RuleNestedSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating rules with nested rule details."""

    entity_details = serializers.SerializerMethodField()
    name = serializers.CharField()
    platform = serializers.PrimaryKeyRelatedField(
        queryset=Platform.objects.all())
    platform_name = serializers.CharField(
        source='platform.name', read_only=True)
    platform_slug = serializers.CharField(
        source='platform.slug', read_only=True)
    rule_details = RuleDetailCreateSerializer(many=True, write_only=True)
    description = serializers.CharField(allow_blank=True, required=False)
    workspace_name = serializers.SerializerMethodField()
    workspace = serializers.IntegerField(
        write_only=True, required=False, allow_null=True)

    def validate_workspace(self, value):
        """Validate workspace field"""
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                # Check workspace access permissions
                try:
                    workspace = Workspace.objects.get(id=value)
                    # Check if user has access to this workspace
                    if not request.user.is_superuser and not request.user.has_workspace_access(value):
                        raise serializers.ValidationError(
                            f"Access denied to workspace {value}")
                    return workspace  # Return workspace object for access later
                except Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
            else:
                # No request context - allow during testing
                try:
                    workspace = Workspace.objects.get(id=value)
                    return workspace  # Return workspace object for access later
                except Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
        return value

    def validate_platform(self, value):
        """Validate platform field"""
        try:
            # Handle both formats: direct ID or dict with ID
            platform_id = value.id if hasattr(value, 'id') else value
            platform = Platform.objects.get(id=platform_id)
            return platform  # Return platform object for access later
        except Platform.DoesNotExist:
            raise serializers.ValidationError(
                f"Platform {value} does not exist")
        except AttributeError:
            raise serializers.ValidationError(
                "Invalid platform format. Expected an ID or a Platform instance.")

    def validate(self, attrs):
        """Validate that all entities in rule_details belong to the same platform."""
        platform = attrs.get('platform')
        rule_details = attrs.get('rule_details', [])

        if platform and rule_details:
            for detail in rule_details:
                entity = detail.get('entity')
                if entity and hasattr(entity, 'platform') and entity.platform != platform:
                    raise serializers.ValidationError(
                        f"Entity '{entity.name}' belongs to platform '{entity.platform.name}' "
                        f"but the rule is for platform '{platform.name}'. "
                        "All entities must belong to the same platform."
                    )

        return attrs

    class Meta:
        model = Rule
        fields = ['id', 'name', 'description', 'status', 'platform',
                  'platform_name', 'platform_slug', 'entity_details', 'rule_details',
                  'workspace', 'workspace_name']

    def create(self, validated_data):
        rule_details_data = validated_data.pop('rule_details')
        # This is a Workspace instance from validation
        workspace = validated_data.pop('workspace')

        # Create the Rule instance - explicitly set workspace and platform
        rule = Rule.objects.create(
            workspace=workspace,  # Workspace instance is used directly
            **validated_data  # platform is included here since it's already a Platform instance
        )

        # Create RuleDetail instances with the same workspace
        for detail_data in rule_details_data:
            RuleDetail.objects.create(
                rule=rule,
                workspace=workspace,
                **detail_data
            )

        return rule

    def update(self, instance, validated_data):
        rule_details_data = validated_data.pop('rule_details', [])
        platform_data = validated_data.pop('platform', None)
        workspace = validated_data.pop('workspace', None)

        # Update rule instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle platform update
        if platform_data:
            platform = platform_data['id'] if isinstance(
                platform_data, dict) else platform_data
            instance.platform = platform

        # Handle workspace update
        if workspace:
            instance.workspace = workspace

        instance.save()

        # Handle rule_details update
        if rule_details_data:
            # Delete existing rule details
            instance.rule_details.all().delete()

            # Create new rule details
            for detail_data in rule_details_data:
                RuleDetail.objects.create(
                    rule=instance,
                    workspace=workspace or instance.workspace,
                    **detail_data
                )

        return instance

    def get_entity_details(self, obj):
        # Get all rule details for this rule
        rule_details = obj.rule_details.all()

        # Create a dictionary to group by entity
        grouped_details = {}

        for detail in rule_details:
            if not detail.entity:
                continue

            entity_id = detail.entity.id

            if entity_id not in grouped_details:
                # Initialize the entity group with entity information safely
                next_entity_id = None
                if detail.entity and detail.entity.next_entity:
                    next_entity_id = detail.entity.next_entity.id

                grouped_details[entity_id] = {
                    'entity': entity_id,
                    'entity_name': detail.entity.name if detail.entity else None,
                    'entity_level': detail.entity.entity_level if detail.entity else None,
                    'next_entity': next_entity_id,
                    'can_generate': True,  # TODO: implement can_generate logic
                    'dimensions': []
                }

            # Add dimension information safely
            if not detail.dimension:
                continue

            dimension_info = {
                'id': detail.id,
                'dimension': detail.dimension.id if detail.dimension else None,
                'dimension_name': detail.dimension.name if detail.dimension else None,
                'dimension_type': detail.dimension.type if detail.dimension else None,
                'dimension_description': detail.dimension.description if detail.dimension else None,
                'dimension_order': detail.dimension_order,
                'is_required': getattr(detail, 'is_required', True),
                'prefix': detail.prefix or '',  # Convert None to empty string
                'suffix': detail.suffix or '',  # Convert None to empty string
                'delimiter': detail.delimiter or '',  # Convert None to empty string
                'effective_delimiter': detail.delimiter or '',  # TODO: implement effective delimiter logic
                'parent_dimension_name': (detail.dimension.parent.name
                                          if detail.dimension and detail.dimension.parent
                                          else None),
                'parent_dimension': (detail.dimension.parent.id
                                     if detail.dimension and detail.dimension.parent
                                     else None),
                'inherits_from_parent': False,  # TODO: implement inheritance detection
                'parent_rule_detail': None,  # TODO: implement parent rule detail lookup
                'dimension_values': [],
                'dimension_value_count': 0,
                'allows_freetext': detail.dimension.type == 'text' if detail.dimension else False,
                'is_dropdown': detail.dimension.type in ['list', 'combobox'] if detail.dimension else False
            }

            # Safely get dimension values
            if detail.dimension:
                try:
                    # Filter dimension values (with defensive check for is_active field)
                    filter_kwargs = {}
                    if hasattr(detail.dimension.dimension_values.model, 'is_active'):
                        filter_kwargs['is_active'] = True

                    dimension_values = [
                        {
                            'id': value.id,
                            'value': value.value,
                            'label': value.label,
                            'utm': value.utm,
                            'description': value.description or '',
                            'is_active': getattr(value, 'is_active', True),
                        } for value in detail.dimension.dimension_values.filter(**filter_kwargs)
                        if value is not None  # Extra safety check
                    ]
                    dimension_info['dimension_values'] = dimension_values
                    dimension_info['dimension_value_count'] = len(dimension_values)
                except (AttributeError, ObjectDoesNotExist) as e:
                    # Log expected errors when accessing dimension values
                    logger.warning(
                        f'Error getting dimension values for dimension {detail.dimension.id}: {e}',
                        extra={
                            'dimension_id': detail.dimension.id,
                            'detail_id': detail.id,
                            'rule_id': obj.id
                        }
                    )
                    dimension_info['dimension_values'] = []
                except Exception as e:
                    # Log unexpected errors and re-raise
                    logger.error(
                        f'Unexpected error getting dimension values: {e}',
                        exc_info=True,
                        extra={
                            'dimension_id': detail.dimension.id if detail.dimension else None,
                            'detail_id': detail.id,
                            'rule_id': obj.id
                        }
                    )
                    raise

            grouped_details[entity_id]['dimensions'].append(dimension_info)

            # combine dimensions to form entity_rule safely
            try:
                dimension_names = [
                    (dim.get('prefix', '') or '') +  # Handle None values
                    (dim.get('dimension_name', '') or '') +
                    (dim.get('suffix', '') or '') +
                    (dim.get('delimiter', '') or '')
                    for dim in sorted(
                        grouped_details[entity_id]['dimensions'],
                        # Default to 0 if missing
                        key=lambda x: x.get('dimension_order', 0)
                    )
                ]
                entity_rule = ''.join(dimension_names)
                grouped_details[entity_id]['entity_rule_preview'] = entity_rule
            except (AttributeError, KeyError, TypeError) as e:
                # Log expected errors when forming entity_rule
                logger.warning(
                    f'Error forming entity_rule for entity {entity_id}: {e}',
                    extra={
                        'entity_id': entity_id,
                        'rule_id': obj.id,
                        'dimensions_count': len(grouped_details[entity_id]['dimensions'])
                    }
                )
                grouped_details[entity_id]['entity_rule_preview'] = ''
            except Exception as e:
                # Log unexpected errors and re-raise
                logger.error(
                    f'Unexpected error forming entity_rule: {e}',
                    exc_info=True,
                    extra={
                        'entity_id': entity_id,
                        'rule_id': obj.id
                    }
                )
                raise

        # Add computed fields to each entity group
        for entity_id, entity_data in grouped_details.items():
            # Add dimension counts
            entity_data['dimension_count'] = len(entity_data['dimensions'])
            entity_data['required_dimension_count'] = sum(
                1 for d in entity_data['dimensions'] if d.get('is_required', True)
            )

            # Add required dimensions list (dimension names)
            entity_data['required_dimensions'] = [
                d['dimension_name']
                for d in entity_data['dimensions']
                if d.get('is_required', True)
            ]

        # Convert dictionary to list
        return list(grouped_details.values())

    def get_workspace_name(self, obj):
        if obj.workspace:
            return obj.workspace.name
        return None
