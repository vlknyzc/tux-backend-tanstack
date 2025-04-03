from rest_framework import serializers
from django.db.models import Max
from .. import models


# # class ConventionSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = models.Convention
# #         fields = ['id', 'name', 'description',
# #                   'status', 'valid_from', 'valid_until']

# #     def validate(self, data):
# #         """
# #         Check that valid_until is after valid_from if provided
# #         """
# #         if data.get('valid_until') and data['valid_until'] < data['valid_from']:
# #             raise serializers.ValidationError({
# #                 "valid_until": "End date must be after start date"
# #             })
# #         return data


# # class ConventionPlatformSerializer(serializers.ModelSerializer):
# #     name = serializers.SerializerMethodField()
# #     platforms = serializers.SerializerMethodField()
# #     description = serializers.SerializerMethodField()
# #     created = serializers.DateTimeField(format="%Y-%m-%d")
# #     last_updated = serializers.DateTimeField(format="%Y-%m-%d")

# #     class Meta:
# #         model = models.ConventionPlatform
# #         fields = [
# #             'id',
# #             'convention',
# #             'name',
# #             'platforms',
# #             'description',
# #             'created',
# #             'last_updated'
# #         ]

# #     def get_name(self, obj):
# #         return obj.convention.name

# #     def get_description(self, obj):
# #         return obj.convention.description

# #     def get_platforms(self, obj):
# #         return [obj.platform.name]


# # class ConventionPlatformDetailSerializer(serializers.ModelSerializer):
# #     platform_name = serializers.SerializerMethodField()
# #     platform_fields = serializers.SerializerMethodField()
# #     convention_name = serializers.SerializerMethodField()

# #     class Meta:
# #         model = models.ConventionPlatform
# #         fields = [
# #             'id',
# #             'convention',
# #             'convention_name',
# #             'platform',
# #             'platform_name',
# #             'platform_fields',
# #             'created',
# #             'last_updated'
# #         ]

# #     def get_platform_name(self, obj):
# #         return obj.platform.name

# #     def get_platform_fields(self, obj):
# #         from .platform import FieldSerializer
# #         fields = models.Field.objects.filter(
# #             platform=obj.platform).order_by('field_level')
# #         return FieldSerializer(fields, many=True).data

# #     def get_convention_name(self, obj):
# #         return obj.convention.name


# class RuleDetailSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = models.RuleDetail
#         fields = ['id', 'rule', 'field', 'dimension']


class RuleDetailSerializer(serializers.ModelSerializer):
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    rule_name = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    parent_dimension_id = serializers.SerializerMethodField()
    parent_dimension_name = serializers.SerializerMethodField()

    field_id = serializers.SerializerMethodField()
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    next_field = serializers.SerializerMethodField()
    in_parent_field = serializers.SerializerMethodField()
    is_max_field_level = serializers.SerializerMethodField()

    class Meta:
        model = models.RuleDetail
        fields = [
            "id",
            "rule",
            "rule_name",
            "platform_id",
            "platform_name",
            "field",
            "field_id",
            "field_name",
            "field_level",
            "next_field",
            "dimension",
            "dimension_name",
            "dimension_type",
            "dimension_order",
            "prefix",
            "suffix",
            "delimiter",
            "parent_dimension_name",
            "parent_dimension_id",
            "in_parent_field",
            "is_max_field_level",
        ]

    def get_field_id(self, obj):
        return obj.field.id

    def get_field_name(self, obj):
        return obj.field.name

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_platform_id(self, obj):
        return obj.rule.platform.id

    def get_platform_name(self, obj):
        return obj.rule.platform.name

    def get_dimension_name(self, obj):
        return obj.dimension.name

    def get_dimension_type(self, obj):
        return obj.dimension.dimension_type

    def get_parent_dimension_name(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.name
        else:
            return None

    def get_parent_dimension_id(self, obj):
        if obj.dimension.parent_id:
            parent = models.Dimension.objects.get(id=obj.dimension.parent_id)
            return parent.id
        else:
            return None

    def get_field_name(self, obj):
        return obj.field.name

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_next_field(self, obj):
        if obj.field.next_field_id:
            next_field = models.Field.objects.get(
                id=obj.field.next_field_id)
            return next_field.name
        else:
            return None

    def get_rule_name(self, obj):
        return obj.rule.name

    def get_in_parent_field(self, obj):
        field_level = obj.field.field_level
        if field_level <= 1:
            return False

        parent_exists = models.RuleDetail.objects.filter(
            # rule__convention=obj.rule.convention,
            rule__field__platform=obj.field.platform,
            dimension=obj.dimension,
            rule__field__field_level=field_level - 1
        ).exists()

        return parent_exists

    def get_is_max_field_level(self, obj):
        max_field_level = models.Field.objects.filter(
            platform=obj.field.platform
        ).aggregate(max_level=Max('field_level'))['max_level']

        return obj.field.field_level == max_field_level


class RuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Rule
        fields = [
            'id',
            # 'convention',
            'platform',
            'status',
            'name',

        ]


class RuleNestedSerializer(serializers.ModelSerializer):
    field_details = RuleDetailSerializer(source='rule_details', many=True)

    class Meta:
        model = models.Rule
        fields = ['id', 'name', 'field_details']
