from rest_framework import serializers
from django.db.models import Max
from .. import models


class RuleNestedSerializer(serializers.ModelSerializer):
    field_details = serializers.SerializerMethodField()
    name = serializers.CharField()  # Remove the source='rule.name'
    platform = serializers.IntegerField(
        source='platform.id')  # Update this line
    platform_name = serializers.CharField(source='platform.name')

    class Meta:
        model = models.Rule
        fields = ['id', 'name', 'status', 'platform',
                  'platform_name', 'field_details']

    def get_field_details(self, obj):
        # Get all rule details for this rule
        rule_details = obj.rule_details.all()

        # Create a dictionary to group by field
        grouped_details = {}

        for detail in rule_details:
            field_id = detail.field.id

            if field_id not in grouped_details:
                # Initialize the field group with field information

                grouped_details[field_id] = {
                    'field_id': field_id,
                    'field_name': detail.field.name,
                    'field_level': detail.field.field_level,
                    'next_field': detail.field.next_field.name if detail.field.next_field_id else None,
                    'dimensions': []
                }

            # Add dimension information
            dimension_info = {
                'id': detail.id,
                'dimension_id': detail.dimension.id,
                'dimension_name': detail.dimension.name,
                'dimension_type': detail.dimension.dimension_type,
                'dimension_order': detail.dimension_order,
                'prefix': detail.prefix,
                'suffix': detail.suffix,
                'delimiter': detail.delimiter,
                'parent_dimension_name': (detail.dimension.parent.name
                                          if detail.dimension.parent_id else None),
                'parent_dimension_id': detail.dimension.parent_id
            }

            grouped_details[field_id]['dimensions'].append(dimension_info)

            # combine dimensions to form field_rule
            dimension_names = [
                dim['prefix'] + dim['dimension_name'] +
                dim['suffix'] + dim['delimiter']
                for dim in sorted(
                    grouped_details[field_id]['dimensions'],
                    key=lambda x: x['dimension_order']
                )
            ]
            field_rule = f"{''.join(dimension_names)}"
            grouped_details[field_id]['field_rule'] = field_rule

        # Convert dictionary to list
        return list(grouped_details.values())
