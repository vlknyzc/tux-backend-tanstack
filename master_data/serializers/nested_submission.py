from rest_framework import serializers
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
import logging
from .. import models
from .string import StringSerializer, StringDetailSerializer
from .submission import SubmissionSerializer

from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class StringDetailNestedCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating string details in nested submissions (POST requests only)"""
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
            "dimension_value",
            "dimension_value_freetext",
        ]


class StringDetailNestedSerializer(serializers.ModelSerializer):
    prefix = serializers.SerializerMethodField()
    suffix = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    dimension_order = serializers.SerializerMethodField()
    dimension_value_label = serializers.SerializerMethodField()
    dimension_value_display = serializers.SerializerMethodField()
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
            "dimension_value_display",
            "dimension_value_label",
            "dimension_value_freetext",
            "prefix",
            "suffix",
            "value",
            "dimension_values",
            "delimiter",
        ]

    def get_dimension_name(self, obj) -> Optional[str]:
        return obj.dimension.name if obj.dimension.name else None

    def get_dimension_type(self, obj) -> Optional[str]:
        return obj.dimension.type if obj.dimension else None

    def get_dimension_order(self, obj) -> Optional[int]:
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

    def get_prefix(self, obj) -> Optional[str]:
        request = self.context.get('request')

        # Case 1: Check for rule_details_dict from list view
        if hasattr(request, 'rule_details_dict') and obj.dimension:
            try:
                rule = obj.string.submission.rule
                key = (rule, obj.dimension)
                if key in request.rule_details_dict:
                    rule_detail = request.rule_details_dict[key]
                    if hasattr(rule_detail, 'prefix'):
                        return rule_detail.prefix
                    return None
            except Exception:
                pass

        # Case 2: Check for rule_details from retrieve view
        if hasattr(request, 'rule_details') and obj.dimension:
            rule_details = request.rule_details
            if obj.dimension in rule_details:
                rule_detail = rule_details[obj.dimension]
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

    def get_suffix(self, obj) -> Optional[str]:
        request = self.context.get('request')

        # Case 1: Check for rule_details_dict from list view
        if hasattr(request, 'rule_details_dict') and obj.dimension:
            try:
                rule = obj.string.submission.rule
                key = (rule, obj.dimension)
                if key in request.rule_details_dict:
                    rule_detail = request.rule_details_dict[key]
                    if hasattr(rule_detail, 'suffix'):
                        return rule_detail.suffix
                    return None
            except Exception:
                pass

        # Case 2: Check for rule_details from retrieve view
        if hasattr(request, 'rule_details') and obj.dimension:
            rule_details = request.rule_details
            if obj.dimension in rule_details:
                rule_detail = rule_details[obj.dimension]
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

    def get_dimension_value_label(self, obj) -> Optional[str]:
        """Get the human-readable label for the dimension value."""
        if obj.dimension_value and hasattr(obj.dimension_value, 'label'):
            return obj.dimension_value.label
        return None

    def get_dimension_value_display(self, obj) -> Optional[str]:
        """Get the actual value for the dimension value."""
        if obj.dimension_value and hasattr(obj.dimension_value, 'value'):
            return obj.dimension_value.value
        return None


class StringNestedCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating strings in nested submissions (POST requests only)"""
    block_items = StringDetailNestedCreateSerializer(
        source='string_details', many=True, required=False)
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    string_value = serializers.CharField(source='value')

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
        ]

    def get_field_name(self, obj) -> Optional[str]:
        return obj.field.name if obj.field else None

    def get_field_level(self, obj) -> Optional[int]:
        return obj.field.field_level if obj.field else None

    def create(self, validated_data):
        block_items_data = validated_data.pop('string_details', [])
        value = validated_data.pop('value', None)
        string_uuid = validated_data.pop('string_uuid', None)

        # Remove non-model fields (no next_field_name or next_field_code to remove)
        validated_data.pop('field_name', None)
        validated_data.pop('field_level', None)

        # Preserve string_uuid if provided
        if string_uuid:
            validated_data['string_uuid'] = string_uuid

        string = models.String.objects.create(value=value, **validated_data)

        for block_item_data in block_items_data:
            # Remove non-model fields
            block_item_data.pop('id', None)  # Remove frontend ID
            block_item_data.pop('dimension_name', None)
            block_item_data.pop('dimension_type', None)
            block_item_data.pop('dimension_order', None)
            block_item_data.pop('value', None)
            block_item_data.pop('dimension_values', None)
            block_item_data.pop('delimiter', None)
            block_item_data.pop('prefix', None)
            block_item_data.pop('suffix', None)

            models.StringDetail.objects.create(
                string=string,
                workspace=string.workspace,
                dimension=block_item_data.get('dimension'),
                dimension_value=block_item_data.get('dimension_value'),
                dimension_value_freetext=block_item_data.get(
                    'dimension_value_freetext')
            )

        return string


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

    def get_field_name(self, obj) -> Optional[str]:
        return obj.field.name if obj.field else None

    def get_field_level(self, obj) -> Optional[int]:
        return obj.field.field_level if obj.field else None

    def create(self, validated_data):
        block_items_data = validated_data.pop('string_details', [])
        value = validated_data.pop('value', None)
        string_uuid = validated_data.pop('string_uuid', None)

        # Remove non-model fields
        validated_data.pop('next_field_name', None)
        validated_data.pop('next_field_code', None)
        validated_data.pop('field_name', None)
        validated_data.pop('field_level', None)

        # Preserve string_uuid if provided
        if string_uuid:
            validated_data['string_uuid'] = string_uuid

        string = models.String.objects.create(value=value, **validated_data)

        for block_item_data in block_items_data:
            # Remove non-model fields
            block_item_data.pop('id', None)  # Remove frontend ID
            block_item_data.pop('dimension_name', None)
            block_item_data.pop('dimension_type', None)
            block_item_data.pop('dimension_order', None)
            block_item_data.pop('value', None)
            block_item_data.pop('dimension_values', None)
            block_item_data.pop('delimiter', None)
            block_item_data.pop('prefix', None)
            block_item_data.pop('suffix', None)

            models.StringDetail.objects.create(
                string=string,
                workspace=string.workspace,
                dimension=block_item_data.get('dimension'),
                dimension_value=block_item_data.get('dimension_value'),
                dimension_value_freetext=block_item_data.get(
                    'dimension_value_freetext')
            )

        return string

    def update(self, instance, validated_data):
        blocks_data = validated_data.pop('submission_strings', [])
        # Extract workspace for proper handling
        workspace = validated_data.pop('workspace', None)
        # Use existing workspace if not provided
        if not workspace:
            workspace = instance.workspace

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
            # Create UUID mapping to preserve parent-child relationships
            uuid_mapping = {}  # old_uuid -> new_uuid

            # First, collect all UUIDs from the payload to build mapping
            for block_data in blocks_data:
                old_uuid = block_data.get('string_uuid')
                if old_uuid:
                    uuid_mapping[old_uuid] = old_uuid  # preserve the same UUID

            # First, delete all existing strings to avoid unique constraint conflicts
            instance.submission_strings.all().delete()

            # Create new strings
            for block_data in blocks_data:
                # Handle nested block_items
                block_items_data = block_data.pop('string_details', [])

                # Extract and preserve string_uuid from frontend
                string_uuid = block_data.pop('string_uuid', None)

                # Update parent_uuid if it exists in our mapping
                parent_uuid = block_data.get('parent_uuid')
                if parent_uuid and parent_uuid in uuid_mapping:
                    block_data['parent_uuid'] = uuid_mapping[parent_uuid]

                # Remove non-model fields
                block_data.pop('field_name', None)
                block_data.pop('field_level', None)
                block_data.pop('next_field_name', None)
                block_data.pop('next_field_code', None)
                block_data.pop('dimensions', None)
                block_data.pop('field_rule', None)

                # Create new string with preserved UUID
                new_string_data = block_data.copy()
                if 'id' in new_string_data:
                    del new_string_data['id']

                # Explicitly set the string_uuid if provided
                if string_uuid:
                    new_string_data['string_uuid'] = string_uuid

                string = models.String.objects.create(
                    submission=instance,
                    workspace=workspace,  # Set workspace on string
                    **new_string_data
                )

                # Create string details
                for detail_data in block_items_data:
                    # Remove non-model fields
                    detail_data.pop('id', None)  # Remove frontend ID
                    detail_data.pop('name', None)
                    detail_data.pop('type', None)
                    detail_data.pop('order', None)
                    raw_value = detail_data.pop('value', None)
                    detail_data.pop('dimension_values', None)
                    detail_data.pop('delimiter', None)
                    detail_data.pop('prefix', None)
                    detail_data.pop('suffix', None)
                    detail_data.pop('dimension_order', None)
                    detail_data.pop('parent_dimension_name', None)
                    detail_data.pop('parent_dimension', None)

                    # Handle dimension_value properly based on dimension type
                    dimension_value_id = detail_data.pop(
                        'dimension_value', None)
                    dimension_id = detail_data.get('dimension')

                    # Reset dimension_value and dimension_value_freetext
                    detail_data['dimension_value'] = None
                    detail_data['dimension_value_freetext'] = None

                    # Case 1: dimension_value ID is provided directly (from frontend)
                    if dimension_value_id:
                        try:
                            # Check if dimension_value_id is already a DimensionValue object (converted by DRF)
                            if hasattr(dimension_value_id, '_meta') and dimension_value_id._meta.model_name == 'dimensionvalue':
                                dimension_value = dimension_value_id
                            else:
                                # It's an ID, so fetch the object
                                dimension_value = models.DimensionValue.objects.get(
                                    id=dimension_value_id)
                            detail_data['dimension_value'] = dimension_value
                        except models.DimensionValue.DoesNotExist:
                            logger.warning(
                                f"DimensionValue {dimension_value_id} not found")

                    # Case 2: raw_value is provided, need to look up dimension value
                    elif dimension_id and raw_value:
                        try:
                            dimension = models.Dimension.objects.get(
                                id=dimension_id)

                            if dimension.type == 'list':
                                # For list type dimensions, look up the DimensionValue
                                dimension_value = models.DimensionValue.objects.filter(
                                    dimension=dimension,
                                    value=raw_value
                                ).first()
                                detail_data['dimension_value'] = dimension_value
                            else:
                                # For text type dimensions, use freetext
                                detail_data['dimension_value_freetext'] = raw_value

                        except models.Dimension.DoesNotExist:
                            logger.warning(
                                f"Dimension {dimension_id} not found")

                    models.StringDetail.objects.create(
                        string=string,
                        workspace=workspace,
                        dimension=detail_data.get('dimension'),
                        dimension_value=detail_data.get('dimension_value'),
                        dimension_value_freetext=detail_data.get(
                            'dimension_value_freetext')
                    )

        return instance


class SubmissionNestedCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating nested submissions (POST requests only)"""
    blocks = StringNestedCreateSerializer(
        source='submission_strings', many=True, required=False)
    rule = serializers.PrimaryKeyRelatedField(
        queryset=models.Rule.objects.all(), required=True)
    selected_parent = serializers.PrimaryKeyRelatedField(
        queryset=models.String.objects.all(),
        required=False,
        allow_null=True,
        source='selected_parent_string'
    )
    workspace = serializers.IntegerField(
        write_only=True, required=False, allow_null=True)

    def validate_workspace(self, value):
        """Validate workspace field"""
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    # Check if user has access to this workspace (skip for anonymous users in DEBUG)
                    if (request.user.is_authenticated and
                        not request.user.is_superuser and
                            not request.user.has_workspace_access(value)):
                        raise serializers.ValidationError(
                            f"Access denied to workspace {value}")
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
            else:
                # No request context - allow during testing
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
        return value

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
            "workspace",
        ]

    def validate_rule(self, value):
        if isinstance(value, dict):
            rule = value.get('id')
            if rule:
                try:
                    return models.Rule.objects.get(id=rule)
                except models.Rule.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Rule with id {rule} does not exist.")
        return value

    def create(self, validated_data):
        blocks_data = validated_data.pop('submission_strings', [])
        # Extract workspace for proper handling
        workspace = validated_data.pop('workspace', None)

        try:
            # Validate required fields
            if not validated_data.get('rule'):
                raise serializers.ValidationError("Rule is required")

            # Check for potential UUID conflicts before creating
            string_uuids = []
            for block_data in blocks_data:
                string_uuid = block_data.get('string_uuid')
                if string_uuid:
                    if string_uuid in string_uuids:
                        raise serializers.ValidationError(
                            f"Duplicate string_uuid: {string_uuid}")
                    string_uuids.append(string_uuid)

                    # Check if UUID already exists in database
                    if models.String.objects.filter(string_uuid=string_uuid).exists():
                        raise serializers.ValidationError(
                            f"String with UUID {string_uuid} already exists")

            # Set workspace directly on validated_data if provided
            if workspace:
                validated_data['workspace'] = workspace

            submission = models.Submission.objects.create(**validated_data)
            logger.info(f"Created submission {submission.id}")

            # Create strings and their details
            for i, block_data in enumerate(blocks_data):
                try:
                    # Handle nested block_items
                    block_items_data = block_data.pop('string_details', [])

                    # Extract and preserve string_uuid from frontend
                    string_uuid = block_data.pop('string_uuid', None)

                    # Remove non-model fields (no next_field_name or next_field_code to remove)
                    block_data.pop('field_name', None)
                    block_data.pop('field_level', None)

                    # Preserve string_uuid if provided
                    if string_uuid:
                        block_data['string_uuid'] = string_uuid

                    # Set parent_uuid from selected_parent_string if provided
                    if submission.selected_parent_string and not block_data.get('parent_uuid'):
                        block_data['parent_uuid'] = submission.selected_parent_string.string_uuid
                        logger.debug(
                            f"Setting parent_uuid to {submission.selected_parent_string.string_uuid} from selected_parent_string")

                    # Validate required fields for string
                    if not block_data.get('field'):
                        raise serializers.ValidationError(
                            f"Field is required for string at index {i}")
                    if not block_data.get('value'):
                        raise serializers.ValidationError(
                            f"Value is required for string at index {i}")

                    # Create string
                    string = models.String.objects.create(
                        submission=submission,
                        workspace=workspace,
                        **block_data
                    )
                    logger.debug(
                        f"Created string {string.id} with UUID {string.string_uuid}")

                    # Create string details
                    for j, detail_data in enumerate(block_items_data):
                        try:
                            # Remove non-model fields
                            detail_data.pop('id', None)  # Remove frontend ID
                            detail_data.pop('dimension_name', None)
                            detail_data.pop('dimension_type', None)
                            detail_data.pop('dimension_order', None)
                            raw_value = detail_data.pop('value', None)
                            detail_data.pop('dimension_values', None)
                            detail_data.pop('delimiter', None)
                            detail_data.pop('prefix', None)
                            detail_data.pop('suffix', None)

                            # Handle dimension_value properly based on dimension type
                            dimension_value_id = detail_data.pop(
                                'dimension_value', None)
                            dimension_id = detail_data.get('dimension')

                            # Reset dimension_value and dimension_value_freetext
                            detail_data['dimension_value'] = None
                            detail_data['dimension_value_freetext'] = None

                            # Case 1: dimension_value ID is provided directly (from frontend)
                            if dimension_value_id:
                                try:
                                    # Check if dimension_value_id is already a DimensionValue object (converted by DRF)
                                    if hasattr(dimension_value_id, '_meta') and dimension_value_id._meta.model_name == 'dimensionvalue':
                                        dimension_value = dimension_value_id
                                    else:
                                        # It's an ID, so fetch the object
                                        dimension_value = models.DimensionValue.objects.get(
                                            id=dimension_value_id)
                                    detail_data['dimension_value'] = dimension_value
                                except models.DimensionValue.DoesNotExist:
                                    logger.warning(
                                        f"DimensionValue {dimension_value_id} not found")

                            # Case 2: raw_value is provided, need to look up dimension value
                            elif dimension_id and raw_value:
                                try:
                                    dimension = models.Dimension.objects.get(
                                        id=dimension_id)

                                    if dimension.type == 'list':
                                        # For list type dimensions, look up the DimensionValue
                                        dimension_value = models.DimensionValue.objects.filter(
                                            dimension=dimension,
                                            value=raw_value
                                        ).first()
                                        detail_data['dimension_value'] = dimension_value
                                    else:
                                        # For text type dimensions, use freetext
                                        detail_data['dimension_value_freetext'] = raw_value

                                except models.Dimension.DoesNotExist:
                                    logger.warning(
                                        f"Dimension {dimension_id} not found")

                            # Validate required fields for string detail
                            if not detail_data.get('dimension'):
                                raise serializers.ValidationError(
                                    f"Dimension is required for string detail at string {i}, detail {j}")

                            models.StringDetail.objects.create(
                                string=string,
                                workspace=workspace,
                                dimension=detail_data.get('dimension'),
                                dimension_value=detail_data.get(
                                    'dimension_value'),
                                dimension_value_freetext=detail_data.get(
                                    'dimension_value_freetext')
                            )
                        except IntegrityError as e:
                            logger.error(
                                f"IntegrityError creating string detail {j} for string {i}: {str(e)}")
                            raise serializers.ValidationError(
                                f"Constraint violation in string detail {j}: {str(e)}")

                except IntegrityError as e:
                    logger.error(
                        f"IntegrityError creating string {i}: {str(e)}")
                    raise serializers.ValidationError(
                        f"Constraint violation in string {i}: {str(e)}")

            return submission

        except IntegrityError as e:
            logger.error(f"IntegrityError in submission creation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in submission creation: {str(e)}")
            raise


class SubmissionNestedSerializer(serializers.ModelSerializer):
    blocks = StringNestedSerializer(
        source='submission_strings', many=True, required=False)
    rule = serializers.PrimaryKeyRelatedField(
        queryset=models.Rule.objects.all(), required=True)
    selected_parent = serializers.PrimaryKeyRelatedField(
        queryset=models.String.objects.all(),
        required=False,
        allow_null=True,
        source='selected_parent_string'
    )
    created_by_name = serializers.SerializerMethodField()
    workspace = serializers.IntegerField(
        write_only=True, required=False, allow_null=True)

    def validate_workspace(self, value):
        """Validate workspace field"""
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    # Check if user has access to this workspace (skip for anonymous users in DEBUG)
                    if (request.user.is_authenticated and
                        not request.user.is_superuser and
                            not request.user.has_workspace_access(value)):
                        raise serializers.ValidationError(
                            f"Access denied to workspace {value}")
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
            else:
                # No request context - allow during testing
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
        return value

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
            "created_by",
            "created_by_name",
            "workspace",
        ]

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def to_representation(self, instance):
        """Override to provide flattened structure matching nested_submissions.json format"""
        # Start with basic submission fields
        ret = {
            'id': instance.id,
            'name': instance.name,
            'selected_parent': instance.selected_parent_string.id if instance.selected_parent_string else None,
            'starting_field': instance.starting_field.id if instance.starting_field else None,
            'description': instance.description,
            'status': instance.status,
        }

        # Rule representation - simplified with just platform ID
        if instance.rule:
            ret['rule'] = {
                'id': instance.rule.id,
                'name': instance.rule.name,
                'platform': instance.rule.platform.id if instance.rule.platform else None,
            }

            # Platform representation - detailed object
            if instance.rule.platform:
                ret['platform'] = {
                    'id': instance.rule.platform.id,
                    'name': instance.rule.platform.name,
                    'slug': instance.rule.platform.slug,
                }

        # Created by representation - as object
        if instance.created_by:
            ret['created_by'] = {
                'id': instance.created_by.id,
                'name': f"{instance.created_by.first_name} {instance.created_by.last_name}".strip()
            }
        else:
            ret['created_by'] = None

        # Collect all related data for flattened arrays
        strings = []
        string_items = []
        fields = []
        dimensions = []
        dimension_values = []

        # Process submission strings
        for string in instance.submission_strings.all():
            # Add field to fields array if not already present
            if string.field and not any(f['id'] == string.field.id for f in fields):
                # Find parent field by looking for field that has this field as next_field
                try:
                    parent_field = models.Field.objects.filter(
                        next_field=string.field).first()
                    parent_id = parent_field.id if parent_field else None
                except Exception:
                    parent_id = None

                fields.append({
                    'id': string.field.id,
                    'name': string.field.name,
                    'field_level': string.field.field_level,
                    'parent': parent_id,
                    'next_field': string.field.next_field.id if string.field.next_field else None,
                })

            # Collect string item IDs for this string
            string_item_ids = []

            # Process string details
            for string_detail in string.string_details.all():
                string_item_ids.append(string_detail.id)

                # Add dimension to dimensions array if not already present
                if string_detail.dimension and not any(d['id'] == string_detail.dimension.id for d in dimensions):
                    dimensions.append({
                        'id': string_detail.dimension.id,
                        'name': string_detail.dimension.name,
                        'type': string_detail.dimension.type,
                    })

                # Add dimension value to dimension_values array if not already present and exists
                if (string_detail.dimension_value and
                        not any(dv['id'] == string_detail.dimension_value.id for dv in dimension_values)):
                    dimension_values.append({
                        'id': string_detail.dimension_value.id,
                        'value': string_detail.dimension_value.value,
                        'label': string_detail.dimension_value.label,
                    })

                # Get rule details for prefix/suffix
                prefix = ""
                suffix = ""
                delimiter = None
                order = 1

                try:
                    if instance.rule and string_detail.dimension:
                        rule_detail = models.RuleDetail.objects.filter(
                            rule=instance.rule,
                            dimension=string_detail.dimension,
                            field=string.field
                        ).first()
                        if rule_detail:
                            prefix = rule_detail.prefix or ""
                            suffix = rule_detail.suffix or ""
                            delimiter = rule_detail.delimiter
                            order = rule_detail.dimension_order or 1
                except Exception:
                    pass

                # Add string item
                string_items.append({
                    'id': string_detail.id,
                    'dimension': string_detail.dimension.id if string_detail.dimension else None,
                    'order': order,
                    'dimension_value': string_detail.dimension_value.id if string_detail.dimension_value else None,
                    'dimension_value_freetext': string_detail.dimension_value_freetext,
                    'prefix': prefix,
                    'suffix': suffix,
                    'delimiter': delimiter,
                })

            # Add string
            strings.append({
                'id': string.id,
                'field': string.field.id if string.field else None,
                'uuid': str(string.string_uuid) if string.string_uuid else None,
                'value': string.value,
                'parent': string.parent.id if string.parent else None,
                'parent_uuid': str(string.parent_uuid) if string.parent_uuid else None,
                'items': string_item_ids,
                'created_by': string.created_by.id if string.created_by else None,
            })

        # Add all flattened arrays to response
        ret['fields'] = fields
        ret['strings'] = strings
        ret['string_items'] = string_items
        ret['dimensions'] = dimensions
        ret['dimension_values'] = dimension_values

        return ret

    def validate_rule(self, value):
        if isinstance(value, dict):
            rule = value.get('id')
            if rule:
                try:
                    return models.Rule.objects.get(id=rule)
                except models.Rule.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Rule with id {rule} does not exist.")
        return value

    def update(self, instance, validated_data):
        blocks_data = validated_data.pop('submission_strings', [])
        # Extract workspace for proper handling
        workspace = validated_data.pop('workspace', None)
        # Use existing workspace if not provided
        if not workspace:
            workspace = instance.workspace

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
            # Create UUID mapping to preserve parent-child relationships
            uuid_mapping = {}  # old_uuid -> new_uuid

            # First, collect all UUIDs from the payload to build mapping
            for block_data in blocks_data:
                old_uuid = block_data.get('string_uuid')
                if old_uuid:
                    uuid_mapping[old_uuid] = old_uuid  # preserve the same UUID

            # First, delete all existing strings to avoid unique constraint conflicts
            instance.submission_strings.all().delete()

            # Create new strings
            for block_data in blocks_data:
                # Handle nested block_items
                block_items_data = block_data.pop('string_details', [])

                # Extract and preserve string_uuid from frontend
                string_uuid = block_data.pop('string_uuid', None)

                # Update parent_uuid if it exists in our mapping
                parent_uuid = block_data.get('parent_uuid')
                if parent_uuid and parent_uuid in uuid_mapping:
                    block_data['parent_uuid'] = uuid_mapping[parent_uuid]

                # Set parent_uuid from selected_parent_string if no explicit parent_uuid provided
                if instance.selected_parent_string and not block_data.get('parent_uuid'):
                    block_data['parent_uuid'] = instance.selected_parent_string.string_uuid
                    logger.debug(
                        f"Setting parent_uuid to {instance.selected_parent_string.string_uuid} from selected_parent_string in update")

                # Remove non-model fields
                block_data.pop('field_name', None)
                block_data.pop('field_level', None)
                block_data.pop('next_field_name', None)
                block_data.pop('next_field_code', None)
                block_data.pop('dimensions', None)
                block_data.pop('field_rule', None)

                # Create new string with preserved UUID
                new_string_data = block_data.copy()
                if 'id' in new_string_data:
                    del new_string_data['id']

                # Explicitly set the string_uuid if provided
                if string_uuid:
                    new_string_data['string_uuid'] = string_uuid

                string = models.String.objects.create(
                    submission=instance,
                    workspace=workspace,  # Set workspace on string
                    **new_string_data
                )

                # Create string details
                for detail_data in block_items_data:
                    # Remove non-model fields
                    detail_data.pop('id', None)  # Remove frontend ID
                    detail_data.pop('name', None)
                    detail_data.pop('type', None)
                    detail_data.pop('order', None)
                    raw_value = detail_data.pop('value', None)
                    detail_data.pop('dimension_values', None)
                    detail_data.pop('delimiter', None)
                    detail_data.pop('prefix', None)
                    detail_data.pop('suffix', None)
                    detail_data.pop('dimension_order', None)
                    detail_data.pop('parent_dimension_name', None)
                    detail_data.pop('parent_dimension', None)

                    # Handle dimension_value properly based on dimension type
                    dimension_value_id = detail_data.pop(
                        'dimension_value', None)
                    dimension_id = detail_data.get('dimension')

                    # Reset dimension_value and dimension_value_freetext
                    detail_data['dimension_value'] = None
                    detail_data['dimension_value_freetext'] = None

                    # Case 1: dimension_value ID is provided directly (from frontend)
                    if dimension_value_id:
                        try:
                            # Check if dimension_value_id is already a DimensionValue object (converted by DRF)
                            if hasattr(dimension_value_id, '_meta') and dimension_value_id._meta.model_name == 'dimensionvalue':
                                dimension_value = dimension_value_id
                            else:
                                # It's an ID, so fetch the object
                                dimension_value = models.DimensionValue.objects.get(
                                    id=dimension_value_id)
                            detail_data['dimension_value'] = dimension_value
                        except models.DimensionValue.DoesNotExist:
                            logger.warning(
                                f"DimensionValue {dimension_value_id} not found")

                    # Case 2: raw_value is provided, need to look up dimension value
                    elif dimension_id and raw_value:
                        try:
                            dimension = models.Dimension.objects.get(
                                id=dimension_id)

                            if dimension.type == 'list':
                                # For list type dimensions, look up the DimensionValue
                                dimension_value = models.DimensionValue.objects.filter(
                                    dimension=dimension,
                                    value=raw_value
                                ).first()
                                detail_data['dimension_value'] = dimension_value
                            else:
                                # For text type dimensions, use freetext
                                detail_data['dimension_value_freetext'] = raw_value

                        except models.Dimension.DoesNotExist:
                            logger.warning(
                                f"Dimension {dimension_id} not found")

                    models.StringDetail.objects.create(
                        string=string,
                        workspace=workspace,
                        dimension=detail_data.get('dimension'),
                        dimension_value=detail_data.get('dimension_value'),
                        dimension_value_freetext=detail_data.get(
                            'dimension_value_freetext')
                    )

        return instance
