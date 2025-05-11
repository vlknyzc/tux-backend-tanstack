from rest_framework import serializers
from django.db import transaction
from .. import models


class RuleDetailNestedSerializer(serializers.ModelSerializer):
    field = serializers.PrimaryKeyRelatedField(
        queryset=models.Field.objects.all())
    dimension = serializers.PrimaryKeyRelatedField(
        queryset=models.Dimension.objects.all())
    dimension_order = serializers.IntegerField()
    field_level = serializers.IntegerField(
        source='field.field_level', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)

    class Meta:
        model = models.RuleDetail
        fields = ['field', 'dimension', 'dimension_order',
                  'prefix', 'suffix', 'delimiter', 'field_level', 'field_name']
        read_only_fields = ['field_level', 'field_name']


class RuleNestedSerializer(serializers.ModelSerializer):
    rule_details = RuleDetailNestedSerializer(many=True)
    platform = serializers.PrimaryKeyRelatedField(
        queryset=models.Platform.objects.all())
    platform_name = serializers.CharField(
        source='platform.name', read_only=True)

    class Meta:
        model = models.Rule
        fields = ['id', 'name', 'description',
                  'platform', 'status', 'rule_details', 'platform_name']
        read_only_fields = ['platform_name']

    @transaction.atomic
    def create(self, validated_data):
        rule_details_data = validated_data.pop('rule_details')
        rule = models.Rule.objects.create(**validated_data)

        for rule_detail_data in rule_details_data:
            models.RuleDetail.objects.create(rule=rule, **rule_detail_data)

        return rule

    @transaction.atomic
    def update(self, instance, validated_data):
        rule_details_data = validated_data.pop('rule_details')

        # Update rule fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Delete existing rule details
        instance.rule_details.all().delete()

        # Create new rule details
        for rule_detail_data in rule_details_data:
            models.RuleDetail.objects.create(rule=instance, **rule_detail_data)

        return instance
