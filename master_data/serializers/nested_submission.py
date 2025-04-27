from rest_framework import serializers
from .. import models
from .string import StringSerializer, StringDetailSerializer
from .submission import SubmissionSerializer


class StringDetailNestedSerializer(serializers.ModelSerializer):
    prefix = serializers.SerializerMethodField()
    suffix = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    dimension_order = serializers.SerializerMethodField()
    value = serializers.CharField(required=False, allow_blank=True)
    dimension_values = serializers.JSONField(required=False, allow_null=True)
    delimiter = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    dimension_value = serializers.PrimaryKeyRelatedField(
        queryset=models.DimensionValue.objects.all(),
        required=False,
        allow_null=True
    )
    dimension_value_freetext = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = models.StringDetail
        fields = [
            "id",
            "dimension",
            "dimension_name",
            "dimension_order",
            "dimension_type",
            "dimension_value",
            "dimension_value_freetext",
            "prefix",
            "suffix",
            "value",
            "dimension_values",

            "delimiter",
        ]

    def get_dimension_name(self, obj):
        return obj.dimension.name if obj.dimension.name else None

    def get_dimension_type(self, obj):
        return obj.dimension.type if obj.dimension else None

    def get_dimension_order(self, obj):
        request = self.context.get('request')

        try:
            rule = obj.string.submission.rule
            field = obj.string.field
            # Get the correct dimension order from RuleDetail
            rule_detail = models.RuleDetail.objects.filter(
                rule=rule,
                field=field,
                dimension=obj.dimension
            ).order_by('dimension_order').first()

            if rule_detail and hasattr(rule_detail, 'dimension_order'):
                return rule_detail.dimension_order

        except Exception:
            pass

        return None

    def get_prefix(self, obj):
        request = self.context.get('request')

        # Case 1: Check for rule_details_dict from list view
        if hasattr(request, 'rule_details_dict') and obj.dimension_id:
            try:
                rule_id = obj.string.submission.rule_id
                key = (rule_id, obj.dimension_id)
                if key in request.rule_details_dict:
                    rule_detail = request.rule_details_dict[key]
                    if hasattr(rule_detail, 'prefix'):
                        return rule_detail.prefix
                    return None
            except Exception:
                pass

        # Case 2: Check for rule_details from retrieve view
        if hasattr(request, 'rule_details') and obj.dimension_id:
            rule_details = request.rule_details
            if obj.dimension_id in rule_details:
                rule_detail = rule_details[obj.dimension_id]
                if hasattr(rule_detail, 'prefix'):
                    return rule_detail.prefix
                return None

        # Case 3: Fallback to database lookup
        try:
            rule = obj.string.submission.rule
            rule_detail = models.RuleDetail.objects.filter(
                rule=rule,
                dimension=obj.dimension
            ).first()
            if rule_detail and hasattr(rule_detail, 'prefix'):
                return rule_detail.prefix
        except Exception:
            pass
        return None

    def get_suffix(self, obj):
        request = self.context.get('request')

        # Case 1: Check for rule_details_dict from list view
        if hasattr(request, 'rule_details_dict') and obj.dimension_id:
            try:
                rule_id = obj.string.submission.rule_id
                key = (rule_id, obj.dimension_id)
                if key in request.rule_details_dict:
                    rule_detail = request.rule_details_dict[key]
                    if hasattr(rule_detail, 'suffix'):
                        return rule_detail.suffix
                    return None
            except Exception:
                pass

        # Case 2: Check for rule_details from retrieve view
        if hasattr(request, 'rule_details') and obj.dimension_id:
            rule_details = request.rule_details
            if obj.dimension_id in rule_details:
                rule_detail = rule_details[obj.dimension_id]
                if hasattr(rule_detail, 'suffix'):
                    return rule_detail.suffix
                return None

        # Case 3: Fallback to database lookup
        try:
            rule = obj.string.submission.rule
            rule_detail = models.RuleDetail.objects.filter(
                rule=rule,
                dimension=obj.dimension
            ).first()
            if rule_detail and hasattr(rule_detail, 'suffix'):
                return rule_detail.suffix
        except Exception:
            pass
        return None


class StringNestedSerializer(serializers.ModelSerializer):
    block_items = StringDetailNestedSerializer(
        source='string_details', many=True, required=False)
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    string_value = serializers.CharField(source='value')
    next_field_name = serializers.CharField(required=False, allow_blank=True)
    next_field_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = models.String
        fields = [
            "id",
            "field",
            "field_name",
            "field_level",
            "string_uuid",
            "string_value",
            "parent_uuid",
            "block_items",
            "next_field_name",
            "next_field_code",
        ]

    def get_field_name(self, obj):
        return obj.field.name if obj.field else None

    def get_field_level(self, obj):
        return obj.field.field_level if obj.field else None

    def create(self, validated_data):
        block_items_data = validated_data.pop('string_details', [])
        value = validated_data.pop('value', None)

        # Remove non-model fields
        validated_data.pop('next_field_name', None)
        validated_data.pop('next_field_code', None)

        string = models.String.objects.create(value=value, **validated_data)

        for block_item_data in block_items_data:
            # Remove non-model fields
            block_item_data.pop('name', None)
            block_item_data.pop('type', None)
            block_item_data.pop('order', None)
            block_item_data.pop('value', None)
            block_item_data.pop('dimension_values', None)
            block_item_data.pop('delimiter', None)
            block_item_data.pop('prefix', None)
            block_item_data.pop('suffix', None)
            block_item_data.pop('dimension_order', None)

            models.StringDetail.objects.create(
                string=string, **block_item_data)

        return string

    def update(self, instance, validated_data):
        block_items_data = validated_data.pop('string_details', [])
        value = validated_data.pop('value', None)

        # Remove non-model fields
        validated_data.pop('next_field_name', None)
        validated_data.pop('next_field_code', None)

        # Update String instance
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if value is not None:
            instance.value = value
        instance.save()

        # Handle block_items
        if block_items_data:
            # Clear existing items if any
            instance.string_details.all().delete()

            # Create new items
            for block_item_data in block_items_data:
                # Remove non-model fields
                block_item_data.pop('name', None)
                block_item_data.pop('type', None)
                block_item_data.pop('order', None)
                block_item_data.pop('value', None)
                block_item_data.pop('dimension_values', None)
                block_item_data.pop('delimiter', None)
                block_item_data.pop('prefix', None)
                block_item_data.pop('suffix', None)
                block_item_data.pop('dimension_order', None)

                # Handle dimension_value_id
                dimension_value_id = block_item_data.pop(
                    'dimension_value_id', None)
                if dimension_value_id:
                    block_item_data['dimension_value'] = dimension_value_id

                models.StringDetail.objects.create(
                    string=instance, **block_item_data)

        return instance


class SubmissionNestedSerializer(serializers.ModelSerializer):
    blocks = StringNestedSerializer(
        source='strings', many=True, required=False)
    rule = serializers.PrimaryKeyRelatedField(
        queryset=models.Rule.objects.all(), required=True)
    selected_parent = serializers.PrimaryKeyRelatedField(
        queryset=models.String.objects.all(),
        required=False,
        allow_null=True,
        source='selected_parent_string'
    )

    class Meta:
        model = models.Submission
        fields = [
            "id",
            "name",
            "selected_parent",
            "starting_field",
            "description",
            "status",
            "rule",
            "blocks",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Convert rule id to detailed representation
        if instance.rule:
            ret['rule'] = {
                'id': instance.rule.id,
                'name': instance.rule.name,
                'platform': instance.rule.platform.name,
            }

        if instance.starting_field:
            ret['starting_field'] = {
                'id': instance.starting_field.id,
                'name': instance.starting_field.name,
                'field_level': instance.starting_field.field_level,
            }
        return ret

    def validate_rule(self, value):
        if isinstance(value, dict):
            rule_id = value.get('id')
            if rule_id:
                try:
                    return models.Rule.objects.get(id=rule_id)
                except models.Rule.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Rule with id {rule_id} does not exist.")
        return value

    def create(self, validated_data):
        blocks_data = validated_data.pop('strings', [])
        submission = models.Submission.objects.create(**validated_data)

        # Create strings and their details
        for block_data in blocks_data:
            # Handle nested block_items
            block_items_data = block_data.pop('string_details', [])

            # Remove non-model fields
            block_data.pop('field_name', None)
            block_data.pop('field_level', None)
            block_data.pop('next_field_name', None)
            block_data.pop('next_field_code', None)

            # Create string
            string = models.String.objects.create(
                submission=submission,
                **block_data
            )

            # Create string details
            for detail_data in block_items_data:
                # Remove non-model fields
                detail_data.pop('name', None)
                detail_data.pop('type', None)
                detail_data.pop('order', None)
                detail_data.pop('value', None)
                detail_data.pop('dimension_values', None)
                detail_data.pop('delimiter', None)
                detail_data.pop('prefix', None)
                detail_data.pop('suffix', None)
                detail_data.pop('dimension_order', None)

                # Handle dimension_value_id
                dimension_value_id = detail_data.pop(
                    'dimension_value_id', None)
                if dimension_value_id:
                    detail_data['dimension_value'] = dimension_value_id

                models.StringDetail.objects.create(
                    string=string,
                    **detail_data
                )

        return submission

    def update(self, instance, validated_data):
        blocks_data = validated_data.pop('strings', [])

        # Handle rule data if it comes as a dict
        rule = validated_data.pop('rule', None)
        if rule is not None:
            instance.rule = rule

        # Update Submission instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle blocks
        if blocks_data:
            # First, delete all existing strings to avoid unique constraint conflicts
            instance.strings.all().delete()

            # Create new strings
            for block_data in blocks_data:
                # Handle nested block_items
                block_items_data = block_data.pop('string_details', [])

                # Remove non-model fields
                block_data.pop('field_name', None)
                block_data.pop('field_level', None)
                block_data.pop('next_field_name', None)
                block_data.pop('next_field_code', None)
                block_data.pop('dimensions', None)
                block_data.pop('field_rule', None)

                # Create new string
                new_string_data = block_data.copy()
                if 'id' in new_string_data:
                    del new_string_data['id']

                string = models.String.objects.create(
                    submission=instance,
                    **new_string_data
                )

                # Create string details
                for detail_data in block_items_data:
                    # Remove non-model fields
                    detail_data.pop('name', None)
                    detail_data.pop('type', None)
                    detail_data.pop('order', None)
                    detail_data.pop('value', None)
                    detail_data.pop('dimension_values', None)
                    detail_data.pop('delimiter', None)
                    detail_data.pop('prefix', None)
                    detail_data.pop('suffix', None)
                    detail_data.pop('dimension_order', None)
                    detail_data.pop('parent_dimension_name', None)
                    detail_data.pop('parent_dimension_id', None)

                    models.StringDetail.objects.create(
                        string=string,
                        **detail_data
                    )

        return instance
