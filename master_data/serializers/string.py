from rest_framework import serializers
from .. import models


class StringSerializer(serializers.ModelSerializer):
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    # convention_name = serializers.SerializerMethodField()
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()

    class Meta:
        model = models.String
        fields = [
            "id",
            "submission",
            "last_updated",
            "created",
            "field",
            "field_name",
            "field_level",
            # "convention",
            # "convention_name",
            "platform_id",
            "platform_name",
            "string_uuid",
            "value",
            "parent",
            "parent_uuid",
        ]

    def get_field_name(self, obj):
        return obj.field.name

    def get_field_level(self, obj):
        return obj.field.field_level

    # def get_convention_name(self, obj):
    #     return obj.convention.name if obj.convention else None

    def get_platform_id(self, obj):
        return obj.field.platform.id if obj.field and obj.field.platform else None

    def get_platform_name(self, obj):
        return obj.field.platform.name if obj.field and obj.field.platform else None


class StringDetailSerializer(serializers.ModelSerializer):
    rule_name = serializers.SerializerMethodField()
    dimension_value_id = serializers.SerializerMethodField()
    dimension_value = serializers.SerializerMethodField()
    dimension_value_label = serializers.SerializerMethodField()
    dimension_id = serializers.SerializerMethodField()
    submission_name = serializers.SerializerMethodField()

    class Meta:
        model = models.StringDetail
        fields = [
            "id",
            "submission_name",
            "string",
            "rule",
            "rule_name",
            "dimension_value_id",
            "dimension_value",
            "dimension_value_label",
            "dimension_value_freetext",
            "dimension_id",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated"]

    def validate(self, data):
        """
        Validate based on dimension type
        """
        rule = data.get('rule')
        if not rule:
            raise serializers.ValidationError({
                "rule": "Rule is required"
            })

        dimension_type = rule.dimension.dimension_type
        dimension_value_id = self.initial_data.get('dimension_value_id')
        dimension_value = self.initial_data.get('dimension_value')
        dimension_value_label = self.initial_data.get('dimension_value_label')
        dimension_value_freetext = self.initial_data.get(
            'dimension_value_freetext')

        # For free text dimensions
        if dimension_type in [models.Dimension.FREE_TEXT, models.Dimension.FREE_TEXT_WITH_VALIDATIONS]:
            if dimension_value_id or dimension_value_label:
                raise serializers.ValidationError({
                    "dimension_value_id": "Cannot set dimension_value_id for free text dimensions",
                    "dimension_value_label": "Cannot set dimension_value_label for free text dimensions"
                })
            # Remove the requirement for dimension_value_freetext
            data['dimension_value'] = None
            return data

        # For mastered dimensions
        if dimension_type == models.Dimension.MASTERED:
            if dimension_value_freetext:
                raise serializers.ValidationError({
                    "dimension_value_freetext": "Cannot set free text for mastered dimensions"
                })
            if not dimension_value_id:
                raise serializers.ValidationError({
                    "dimension_value_id": "Dimension value ID is required for mastered dimensions"
                })

            try:
                dimension_value = models.DimensionValue.objects.get(
                    id=dimension_value_id)

                # If other fields are provided, validate they match
                if dimension_value and dimension_value.dimension_value != dimension_value:
                    raise serializers.ValidationError({
                        "dimension_value": f"Value '{dimension_value}' does not match DimensionValue with id {dimension_value_id}"
                    })

                if dimension_value_label and dimension_value.dimension_value_label != dimension_value_label:
                    raise serializers.ValidationError({
                        "dimension_value_label": f"Label '{dimension_value_label}' does not match DimensionValue with id {dimension_value_id}"
                    })

                data['dimension_value'] = dimension_value

            except models.DimensionValue.DoesNotExist:
                raise serializers.ValidationError({
                    "dimension_value_id": f"DimensionValue with id {dimension_value_id} does not exist"
                })

        return data

    def create(self, validated_data):
        # Remove only the extra fields that aren't in the model
        validated_data.pop('dimension_value_id', None)
        validated_data.pop('dimension_value_label', None)

        # Note: Don't pop 'dimension_value' as it contains the JunkDimension instance
        # that was set in the validate method

        # Create the StringItem instance
        string_detail = models.StringDetail.objects.create(**validated_data)
        return string_detail

    def get_rule_name(self, obj):
        return obj.rule.name if obj.rule else None

    def get_submission_name(self, obj):
        return obj.string.submission.name if obj.string and obj.string.submission else None

    def get_dimension_id(self, obj):
        return obj.rule.dimension.id if obj.rule and obj.rule.dimension else None

    def get_dimension_value_id(self, obj):
        return obj.dimension_value.id if obj.dimension_value else None

    def get_dimension_value(self, obj):
        return obj.dimension_value.dimension_value if obj.dimension_value else None

    def get_dimension_value_label(self, obj):
        return obj.dimension_value.dimension_value_label if obj.dimension_value else None
