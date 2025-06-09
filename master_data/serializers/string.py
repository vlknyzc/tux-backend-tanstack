from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .. import models
from ..services import StringGenerationService, NamingConventionError


class StringSerializer(serializers.ModelSerializer):
    field_name = serializers.SerializerMethodField()
    field_level = serializers.SerializerMethodField()
    platform_id = serializers.SerializerMethodField()
    platform_name = serializers.SerializerMethodField()
    platform_slug = serializers.SerializerMethodField()
    submission_name = serializers.SerializerMethodField()
    rule_id = serializers.SerializerMethodField()
    rule_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    workspace_id = serializers.SerializerMethodField()

    # New fields for enhanced business logic
    dimension_values = serializers.SerializerMethodField()
    hierarchy_path = serializers.SerializerMethodField()
    can_have_children = serializers.SerializerMethodField()
    suggested_child_field = serializers.SerializerMethodField()
    naming_conflicts = serializers.SerializerMethodField()

    # Workspace field for write operations
    workspace = serializers.IntegerField(
        write_only=True, required=False, allow_null=True)

    def validate_workspace(self, value):
        """Validate workspace field and user access"""
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    # Check if user has access to this workspace
                    if not request.user.is_superuser and not request.user.has_workspace_access(value):
                        raise serializers.ValidationError(
                            f"Access denied to workspace {value}")
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
            else:
                # Allow without request context during testing
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
        return value

    def validate_submission(self, value):
        """Validate that submission belongs to accessible workspace"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(value.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to submission's workspace")
        return value

    def validate_field(self, value):
        """Validate that field belongs to accessible workspace"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(value.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to field's workspace")
        return value

    def validate_parent(self, value):
        """Validate that parent string belongs to accessible workspace"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(value.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to parent string's workspace")
        return value

    def validate(self, attrs):
        """Cross-field validation for workspace consistency"""
        # Validate related objects belong to same workspace
        submission = attrs.get('submission')
        field = attrs.get('field')
        parent = attrs.get('parent')

        if submission and field:
            if submission.workspace_id != field.workspace_id:
                raise serializers.ValidationError(
                    "Submission and field must belong to the same workspace"
                )

        if parent and submission:
            if parent.workspace_id != submission.workspace_id:
                raise serializers.ValidationError(
                    "Parent string and submission must belong to the same workspace"
                )

        return attrs

    class Meta:
        model = models.String
        fields = [
            "id",
            "submission",
            "submission_name",
            "rule_id",
            "rule_name",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
            "field",
            "field_name",
            "field_level",
            "platform_id",
            "platform_name",
            "platform_slug",
            "string_uuid",
            "value",
            "parent",
            "parent_uuid",
            "workspace",
            "workspace_id",
            "workspace_name",
            # New business logic fields
            "is_auto_generated",
            "generation_metadata",
            "dimension_values",
            "hierarchy_path",
            "can_have_children",
            "suggested_child_field",
            "naming_conflicts",
        ]
        read_only_fields = ["string_uuid", "rule_id", "created",
                            "last_updated", "workspace_name", "workspace_id"]

    def get_field_name(self, obj):
        return obj.field.name

    def get_submission_name(self, obj):
        return obj.submission.name if obj.submission else None

    def get_platform_name(self, obj):
        return obj.field.platform.name if obj.field and obj.field.platform else None

    def get_field_level(self, obj):
        return obj.field.field_level

    def get_platform_id(self, obj):
        return obj.field.platform.id if obj.field and obj.field.platform else None

    def get_platform_slug(self, obj):
        return obj.field.platform.slug if obj.field and obj.field.platform else None

    def get_rule_id(self, obj):
        return obj.submission.rule.id if obj.submission and obj.submission.rule else None

    def get_rule_name(self, obj):
        return obj.submission.rule.name if obj.submission and obj.submission.rule else None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_workspace_name(self, obj):
        return obj.workspace.name if obj.workspace else None

    def get_workspace_id(self, obj):
        return obj.workspace.id if obj.workspace else None

    def get_dimension_values(self, obj):
        """Get dimension values used to generate this string."""
        return obj.get_dimension_values()

    def get_hierarchy_path(self, obj):
        """Get the hierarchy path for this string."""
        path = obj.get_hierarchy_path()
        return [{"id": s.id, "value": s.value, "field_level": s.field.field_level} for s in path]

    def get_can_have_children(self, obj):
        """Check if this string can have child strings."""
        return obj.can_have_children()

    def get_suggested_child_field(self, obj):
        """Get suggested child field for creating child strings."""
        child_field = obj.suggest_child_field()
        if child_field:
            return {"id": child_field.id, "name": child_field.name, "field_level": child_field.field_level}
        return None

    def get_naming_conflicts(self, obj):
        """Get any naming conflicts for this string."""
        return obj.check_naming_conflicts()


class StringDetailSerializer(serializers.ModelSerializer):
    dimension_value_display = serializers.SerializerMethodField()
    dimension_value_label = serializers.SerializerMethodField()
    dimension_name = serializers.SerializerMethodField()
    dimension_type = serializers.SerializerMethodField()
    submission_name = serializers.SerializerMethodField()
    effective_value = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    workspace_id = serializers.SerializerMethodField()

    # Workspace field for write operations
    workspace = serializers.IntegerField(
        write_only=True, required=False, allow_null=True)

    def validate_workspace(self, value):
        """Validate workspace field and user access"""
        if value is not None:
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    # Check if user has access to this workspace
                    if not request.user.is_superuser and not request.user.has_workspace_access(value):
                        raise serializers.ValidationError(
                            f"Access denied to workspace {value}")
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
            else:
                # Allow without request context during testing
                try:
                    workspace = models.Workspace.objects.get(id=value)
                    return workspace
                except models.Workspace.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Workspace {value} does not exist")
        return value

    def validate_string(self, value):
        """Validate that string belongs to accessible workspace"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(value.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to string's workspace")
        return value

    def validate_dimension(self, value):
        """Validate that dimension belongs to accessible workspace"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(value.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to dimension's workspace")
        return value

    def validate_dimension_value(self, value):
        """Validate that dimension value belongs to accessible workspace"""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(value.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to dimension value's workspace")
        return value

    def validate(self, attrs):
        """Cross-field validation for workspace consistency"""
        string_obj = attrs.get('string')
        dimension = attrs.get('dimension')
        dimension_value = attrs.get('dimension_value')

        if string_obj and dimension:
            if string_obj.workspace_id != dimension.workspace_id:
                raise serializers.ValidationError(
                    "String and dimension must belong to the same workspace"
                )

        if dimension and dimension_value:
            if dimension.workspace_id != dimension_value.workspace_id:
                raise serializers.ValidationError(
                    "Dimension and dimension value must belong to the same workspace"
                )

        return attrs

    class Meta:
        model = models.StringDetail
        fields = [
            "id",
            "submission_name",
            "string",
            "dimension",
            "dimension_name",
            "dimension_type",
            "dimension_value",
            "dimension_value_display",
            "dimension_value_label",
            "dimension_value_freetext",
            "effective_value",
            "workspace",
            "workspace_id",
            "workspace_name",
            "created_by",
            "created_by_name",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated",
                            "workspace_name", "workspace_id"]

    def get_submission_name(self, obj):
        return obj.string.submission.name if obj.string and obj.string.submission else None

    def get_dimension_name(self, obj):
        return obj.dimension.name if obj.dimension else None

    def get_dimension_type(self, obj):
        return obj.dimension.type if obj.dimension else None

    def get_dimension_value_display(self, obj):
        return obj.dimension_value.value if obj.dimension_value else None

    def get_dimension_value_label(self, obj):
        return obj.dimension_value.label if obj.dimension_value else None

    def get_effective_value(self, obj):
        """Get the effective value (either from dimension_value or freetext)."""
        return obj.get_effective_value()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_workspace_name(self, obj):
        return obj.workspace.name if obj.workspace else None

    def get_workspace_id(self, obj):
        return obj.workspace.id if obj.workspace else None


class StringGenerationRequestSerializer(serializers.Serializer):
    """Serializer for string generation requests."""
    submission_id = serializers.IntegerField()
    field_id = serializers.IntegerField()
    dimension_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="Dictionary mapping dimension names to their values"
    )
    parent_string_id = serializers.IntegerField(
        required=False, allow_null=True)

    def validate_submission_id(self, value):
        """Validate that submission exists and user has access to its workspace"""
        try:
            submission = models.Submission.objects.get(id=value)
            # Check workspace access
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(submission.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to submission's workspace")
        except models.Submission.DoesNotExist:
            raise serializers.ValidationError("Submission does not exist")
        return value

    def validate_field_id(self, value):
        """Validate that field exists and user has access to its workspace"""
        try:
            field = models.Field.objects.get(id=value)
            # Check workspace access
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(field.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to field's workspace")
        except models.Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")
        return value

    def validate_parent_string_id(self, value):
        """Validate that parent string exists and user has access to its workspace"""
        if value is not None:
            try:
                parent_string = models.String.objects.get(id=value)
                # Check workspace access
                request = self.context.get('request')
                if request and hasattr(request, 'user') and not request.user.is_superuser:
                    if not request.user.has_workspace_access(parent_string.workspace_id):
                        raise serializers.ValidationError(
                            "Access denied to parent string's workspace")
            except models.String.DoesNotExist:
                raise serializers.ValidationError(
                    "Parent string does not exist")
        return value

    def validate(self, attrs):
        """Cross-field validation with workspace awareness"""
        try:
            submission = models.Submission.objects.get(
                id=attrs['submission_id'])
            field = models.Field.objects.get(id=attrs['field_id'])

            # Validate submission and field belong to same workspace
            if submission.workspace_id != field.workspace_id:
                raise serializers.ValidationError(
                    "Submission and field must belong to the same workspace"
                )

            # Validate rule and field belong to same platform
            if submission.rule.platform != field.platform:
                raise serializers.ValidationError(
                    "Rule and field must belong to the same platform"
                )

            # Validate parent string workspace consistency
            parent_string_id = attrs.get('parent_string_id')
            if parent_string_id:
                parent_string = models.String.objects.get(id=parent_string_id)
                if parent_string.workspace_id != submission.workspace_id:
                    raise serializers.ValidationError(
                        "Parent string and submission must belong to the same workspace"
                    )

            # Validate dimension values
            validation_errors = StringGenerationService.validate_dimension_values(
                submission.rule, field, attrs['dimension_values']
            )
            if validation_errors:
                raise serializers.ValidationError({
                    "dimension_values": validation_errors
                })

        except models.Submission.DoesNotExist:
            raise serializers.ValidationError("Submission does not exist")
        except models.Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")
        except models.String.DoesNotExist:
            raise serializers.ValidationError("Parent string does not exist")

        return attrs


class StringRegenerationSerializer(serializers.Serializer):
    """Serializer for string regeneration requests."""
    dimension_values = serializers.DictField(
        child=serializers.CharField(),
        help_text="New dimension values to use for regeneration"
    )


class StringConflictCheckSerializer(serializers.Serializer):
    """Serializer for checking naming conflicts."""
    rule_id = serializers.IntegerField()
    field_id = serializers.IntegerField()
    proposed_value = serializers.CharField()
    exclude_string_id = serializers.IntegerField(
        required=False, allow_null=True)

    def validate_rule_id(self, value):
        """Validate that rule exists and user has access to its workspace"""
        try:
            rule = models.Rule.objects.get(id=value)
            # Check workspace access
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(rule.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to rule's workspace")
        except models.Rule.DoesNotExist:
            raise serializers.ValidationError("Rule does not exist")
        return value

    def validate_field_id(self, value):
        """Validate that field exists and user has access to its workspace"""
        try:
            field = models.Field.objects.get(id=value)
            # Check workspace access
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(field.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to field's workspace")
        except models.Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")
        return value

    def validate_exclude_string_id(self, value):
        """Validate that excluded string exists and user has access to its workspace"""
        if value is not None:
            try:
                string = models.String.objects.get(id=value)
                # Check workspace access
                request = self.context.get('request')
                if request and hasattr(request, 'user') and not request.user.is_superuser:
                    if not request.user.has_workspace_access(string.workspace_id):
                        raise serializers.ValidationError(
                            "Access denied to string's workspace")
            except models.String.DoesNotExist:
                raise serializers.ValidationError("String does not exist")
        return value

    def validate(self, attrs):
        """Cross-field validation with workspace awareness"""
        try:
            rule = models.Rule.objects.get(id=attrs['rule_id'])
            field = models.Field.objects.get(id=attrs['field_id'])

            # Validate rule and field belong to same workspace
            if rule.workspace_id != field.workspace_id:
                raise serializers.ValidationError(
                    "Rule and field must belong to the same workspace"
                )

        except models.Rule.DoesNotExist:
            raise serializers.ValidationError("Rule does not exist")
        except models.Field.DoesNotExist:
            raise serializers.ValidationError("Field does not exist")

        return attrs


class StringBulkGenerationRequestSerializer(serializers.Serializer):
    """Serializer for bulk string generation."""
    submission_id = serializers.IntegerField()
    generation_requests = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of generation requests with field_id and dimension_values"
    )

    def validate_submission_id(self, value):
        """Validate that submission exists and user has access to its workspace"""
        try:
            submission = models.Submission.objects.get(id=value)
            # Check workspace access
            request = self.context.get('request')
            if request and hasattr(request, 'user') and not request.user.is_superuser:
                if not request.user.has_workspace_access(submission.workspace_id):
                    raise serializers.ValidationError(
                        "Access denied to submission's workspace")
        except models.Submission.DoesNotExist:
            raise serializers.ValidationError("Submission does not exist")
        return value

    def validate_generation_requests(self, value):
        """Validate each generation request in the list with workspace awareness"""
        for request in value:
            if 'field_id' not in request:
                raise serializers.ValidationError(
                    "Each request must have field_id")
            if 'dimension_values' not in request:
                raise serializers.ValidationError(
                    "Each request must have dimension_values")

            # Validate field access
            field_id = request.get('field_id')
            if field_id:
                try:
                    field = models.Field.objects.get(id=field_id)
                    # Check workspace access
                    request_context = self.context.get('request')
                    if request_context and hasattr(request_context, 'user') and not request_context.user.is_superuser:
                        if not request_context.user.has_workspace_access(field.workspace_id):
                            raise serializers.ValidationError(
                                f"Access denied to field {field_id}'s workspace")
                except models.Field.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Field {field_id} does not exist")
        return value

    def validate(self, attrs):
        """Cross-field validation with workspace awareness"""
        try:
            submission = models.Submission.objects.get(
                id=attrs['submission_id'])

            # Validate all fields belong to same workspace as submission
            for request in attrs['generation_requests']:
                field_id = request.get('field_id')
                if field_id:
                    field = models.Field.objects.get(id=field_id)
                    if field.workspace_id != submission.workspace_id:
                        raise serializers.ValidationError(
                            f"Field {field_id} and submission must belong to the same workspace"
                        )

        except models.Submission.DoesNotExist:
            raise serializers.ValidationError("Submission does not exist")
        except models.Field.DoesNotExist:
            raise serializers.ValidationError(
                "One or more fields do not exist")

        return attrs
