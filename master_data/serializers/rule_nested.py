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

    class Meta:
        model = models.Rule
        fields = ['id', 'name', 'description', 'status', 'platform',
                  'platform_name', 'platform_slug', 'field_details', 'rule_details']

    def create(self, validated_data):
        rule_details_data = validated_data.pop('rule_details')
        platform_data = validated_data.pop('platform')

        # Create the Rule instance
        rule = models.Rule.objects.create(
            platform_id=platform_data['id'],
            **validated_data
        )

        # Create RuleDetail instances
        for detail_data in rule_details_data:
            models.RuleDetail.objects.create(rule=rule, **detail_data)

        return rule

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
                    'next_field': detail.field.next_field.name if detail.field.next_field_id else None,
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
                                          if detail.dimension.parent_id else None),
                'parent_dimension_id': detail.dimension.parent_id,
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
