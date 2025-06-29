from rest_framework import serializers
from django.db.models import Max
from .. import models


class RuleDetailCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RuleDetail
        fields = ['field', 'dimension', 'dimension_order',
                  'prefix', 'suffix', 'delimiter']


class RuleNestedSerializer(serializers.ModelSerializer):
    field_details = serializers.SerializerMethodField()
    name = serializers.CharField()
    platform = serializers.PrimaryKeyRelatedField(
        queryset=models.Platform.objects.all())
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
                    workspace = models.Workspace.objects.get(id=value)
                    # Check if user has access to this workspace
                    if not request.user.is_superuser and not request.user.has_workspace_access(value):
                        raise serializers.ValidationError(
                            f"Access denied to workspace {value}")
                    return workspace  # Return workspace object for access later
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
            else:
                # No request context - allow during testing
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    return workspace  # Return workspace object for access later
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
        return value

    def validate_platform(self, value):
        """Validate platform field"""
        try:
            # Handle both formats: direct ID or dict with ID
            platform_id = value.id if hasattr(value, 'id') else value
            platform = models.Platform.objects.get(id=platform_id)
            return platform  # Return platform object for access later
        except models.Platform.DoesNotExist:
            raise serializers.ValidationError(
                f"Platform {value} does not exist")
        except AttributeError:
            raise serializers.ValidationError(
                "Invalid platform format. Expected an ID or a Platform instance.")

    class Meta:
        model = models.Rule
        fields = ['id', 'name', 'description', 'status', 'platform',
                  'platform_name', 'platform_slug', 'field_details', 'rule_details',
                  'workspace', 'workspace_name']

    def create(self, validated_data):
        rule_details_data = validated_data.pop('rule_details')
        # This is now a Platform instance
        platform = validated_data.get('platform')
        # This is a Workspace instance from validation
        workspace = validated_data.pop('workspace')

        # Create the Rule instance - explicitly set workspace and platform
        rule = models.Rule.objects.create(
            workspace=workspace,  # Workspace instance is used directly
            **validated_data  # platform is included here since it's already a Platform instance
        )

        # Create RuleDetail instances with the same workspace
        for detail_data in rule_details_data:
            models.RuleDetail.objects.create(
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
                models.RuleDetail.objects.create(
                    rule=instance,
                    workspace=workspace or instance.workspace,
                    **detail_data
                )

        return instance

    def get_field_details(self, obj):
        # Get all rule details for this rule
        rule_details = obj.rule_details.all()

        # Create a dictionary to group by field
        grouped_details = {}

        for detail in rule_details:
            if not detail.field:
                continue

            field = detail.field.id

            if field not in grouped_details:
                # Initialize the field group with field information safely
                next_field_name = None
                if detail.field and detail.field.next_field:
                    next_field_name = detail.field.next_field.name

                grouped_details[field] = {
                    'field': field,
                    'field_name': detail.field.name if detail.field else None,
                    'field_level': detail.field.field_level if detail.field else None,
                    'next_field': next_field_name,
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
                'dimension_order': detail.dimension_order,
                'prefix': detail.prefix or '',  # Convert None to empty string
                'suffix': detail.suffix or '',  # Convert None to empty string
                'delimiter': detail.delimiter or '',  # Convert None to empty string
                'parent_dimension_name': (detail.dimension.parent.name
                                          if detail.dimension and detail.dimension.parent
                                          else None),
                'parent_dimension': (detail.dimension.parent.id
                                     if detail.dimension and detail.dimension.parent
                                     else None),
                'dimension_values': []
            }

            # Safely get dimension values
            if detail.dimension:
                try:
                    dimension_info['dimension_values'] = [
                        {
                            'id': value.id,
                            'value': value.value,
                            'label': value.label,
                            'utm': value.utm,
                        } for value in detail.dimension.dimension_values.all()
                        if value is not None  # Extra safety check
                    ]
                except Exception:
                    # If there's any error getting dimension values, use empty list
                    dimension_info['dimension_values'] = []

            grouped_details[field]['dimensions'].append(dimension_info)

            # combine dimensions to form field_rule safely
            try:
                dimension_names = [
                    (dim.get('prefix', '') or '') +  # Handle None values
                    (dim.get('dimension_name', '') or '') +
                    (dim.get('suffix', '') or '') +
                    (dim.get('delimiter', '') or '')
                    for dim in sorted(
                        grouped_details[field]['dimensions'],
                        # Default to 0 if missing
                        key=lambda x: x.get('dimension_order', 0)
                    )
                ]
                field_rule = ''.join(dimension_names)
                grouped_details[field]['field_rule'] = field_rule
            except Exception:
                # If there's any error forming the field_rule, use empty string
                grouped_details[field]['field_rule'] = ''

        # Convert dictionary to list
        return list(grouped_details.values())

    def get_workspace_name(self, obj):
        if obj.workspace:
            return obj.workspace.name
        return None
