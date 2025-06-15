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
    platform = serializers.IntegerField(source='platform.id')
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

    class Meta:
        model = models.Rule
        fields = ['id', 'name', 'description', 'status', 'platform',
                  'platform_name', 'platform_slug', 'field_details', 'rule_details',
                  'workspace', 'workspace_name']

    def create(self, validated_data):
        rule_details_data = validated_data.pop('rule_details')
        platform_data = validated_data.pop(
            'platform')  # This is a dict {'id': 1}
        # Remove workspace from validated_data - this is a Workspace object from validation
        workspace = validated_data.pop('workspace')

        # Extract platform ID from the dictionary
        platform = platform_data['id'] if isinstance(
            platform_data, dict) else platform_data

        # Create the Rule instance - explicitly set workspace and platform
        rule = models.Rule.objects.create(
            platform=platform,
            workspace=workspace,  # Pass the workspace object directly
            **validated_data  # Now workspace is already removed
        )

        # Create RuleDetail instances with the same workspace
        for detail_data in rule_details_data:
            models.RuleDetail.objects.create(
                rule=rule,
                workspace=workspace,  # Pass the workspace object directly
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
            field = detail.field.id

            if field not in grouped_details:
                # Initialize the field group with field information

                grouped_details[field] = {
                    'field': field,
                    'field_name': detail.field.name,
                    'field_level': detail.field.field_level,
                    'next_field': detail.field.next_field.name if detail.field.next_field else None,
                    'dimensions': []
                }

            # Add dimension information
            dimension_info = {
                'id': detail.id,
                'dimension': detail.dimension.id,
                'dimension_name': detail.dimension.name,
                'dimension_type': detail.dimension.type,
                'dimension_order': detail.dimension_order,
                'prefix': detail.prefix or '',  # Convert None to empty string
                'suffix': detail.suffix or '',  # Convert None to empty string
                'delimiter': detail.delimiter or '',  # Convert None to empty string
                'parent_dimension_name': (detail.dimension.parent.name
                                          if detail.dimension.parent else None),
                'parent_dimension': detail.dimension.parent,
                'dimension_values': [
                    {
                        'id': value.id,
                        'value': value.value,
                        'label': value.label,
                        'utm': value.utm,
                    } for value in detail.dimension.dimension_values.all()
                ]
            }

            grouped_details[field]['dimensions'].append(dimension_info)

            # combine dimensions to form field_rule
            dimension_names = [
                (dim.get('prefix', '') or '') +  # Handle None values
                (dim.get('dimension_name', '') or '') +
                (dim.get('suffix', '') or '') +
                (dim.get('delimiter', '') or '')
                for dim in sorted(
                    grouped_details[field]['dimensions'],
                    key=lambda x: x['dimension_order']
                )
            ]
            field_rule = ''.join(dimension_names)
            grouped_details[field]['field_rule'] = field_rule

        # Convert dictionary to list
        return list(grouped_details.values())

    def get_workspace_name(self, obj):
        if obj.workspace:
            return obj.workspace.name
        return None
