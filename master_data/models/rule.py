"""
Rule models for the master_data app.
Handles naming convention rules and their detailed configurations.
"""

from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

from .base import TimeStampModel, WorkspaceMixin
from ..constants import (
    LONG_NAME_LENGTH, DESCRIPTION_LENGTH, PREFIX_SUFFIX_LENGTH,
    DELIMITER_LENGTH, STANDARD_NAME_LENGTH, SLUG_LENGTH, StatusChoices
)
from master_data.utils import generate_unique_slug


class RuleQuerySet(models.QuerySet):
    """Custom QuerySet for Rule model."""

    def active(self):
        """Filter for active rules only."""
        return self.filter(status=StatusChoices.ACTIVE)

    def for_platform(self, platform):
        """Filter rules for a specific platform."""
        return self.filter(platform=platform)

    def with_details(self):
        """Prefetch rule details for efficient access."""
        return self.prefetch_related('rule_details__field', 'rule_details__dimension')


class RuleManager(models.Manager):
    """Custom manager for Rule model."""

    def get_queryset(self):
        # Import here to avoid circular import
        from .base import WorkspaceManager
        return RuleQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def for_platform(self, platform):
        return self.get_queryset().for_platform(platform)


# Temporarily use custom manager
class WorkspaceRuleManager(RuleManager):
    """Custom manager that extends RuleManager with workspace filtering"""

    def get_queryset(self):
        from .base import get_current_workspace, _thread_locals
        queryset = RuleQuerySet(self.model, using=self._db)
        # Auto-filter by workspace if context is set and user is not superuser
        current_workspace = get_current_workspace()
        if current_workspace and not getattr(_thread_locals, 'is_superuser', False):
            queryset = queryset.filter(workspace_id=current_workspace)
        return queryset

    def all_workspaces(self):
        """Get queryset without workspace filtering (for superusers)"""
        return RuleQuerySet(self.model, using=self._db)

    def for_workspace(self, workspace_id):
        """Filter queryset by specific workspace"""
        return RuleQuerySet(self.model, using=self._db).filter(workspace_id=workspace_id)


class Rule(TimeStampModel, WorkspaceMixin):
    """
    Represents a naming convention rule for a specific platform.

    Rules define how to combine dimension values to create standardized
    naming strings. Each rule can have multiple RuleDetails that specify
    the exact formatting and ordering.
    """

    # Relationships
    platform = models.ForeignKey(
        "master_data.Platform",
        on_delete=models.CASCADE,
        related_name="rules",
        help_text="Platform this rule applies to"
    )

    # Fields
    name = models.CharField(
        max_length=LONG_NAME_LENGTH,
        help_text="Name of this naming rule"
    )
    slug = models.SlugField(
        max_length=SLUG_LENGTH,
        blank=True,
        help_text="URL-friendly version of the name (auto-generated)"
    )
    description = models.TextField(
        max_length=DESCRIPTION_LENGTH,
        null=True,
        blank=True,
        help_text="Description of what this rule generates"
    )
    status = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        help_text="Current status of this rule"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default rule for the platform"
    )

    # Custom manager
    objects = WorkspaceRuleManager()

    class Meta:
        verbose_name = "Rule"
        verbose_name_plural = "Rules"
        # Unique per workspace
        unique_together = [('workspace', 'platform', 'name')]
        ordering = ['workspace', 'platform', 'name']
        indexes = [
            models.Index(fields=['workspace', 'platform', 'status']),
            models.Index(fields=['workspace', 'is_default']),
        ]

    def save(self, *args, **kwargs):
        """Override save to generate slug automatically."""
        if not self.slug:
            self.slug = generate_unique_slug(self, 'name', 'slug', SLUG_LENGTH)
        super().save(*args, **kwargs)

    def clean(self):
        """Validate rule configuration."""
        super().clean()

        # Ensure only one default rule per platform per workspace
        if self.is_default:
            existing_default = Rule.objects.filter(
                workspace=self.workspace,
                platform=self.platform,
                is_default=True
            ).exclude(pk=self.pk)

            if existing_default.exists():
                raise ValidationError(
                    f"Platform '{self.platform.name}' already has a default rule in this workspace: "
                    f"'{existing_default.first().name}'"
                )

    def __str__(self):
        default_indicator = " (Default)" if self.is_default else ""
        return f"{self.name} - {self.platform.name}{default_indicator}"

    def validate_configuration(self):
        """
        Validate that this rule has a proper configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        from ..services import NamingPatternValidator
        return NamingPatternValidator.validate_rule_configuration(self)

    def get_preview(self, field, sample_values):
        """
        Generate a preview of what naming would look like with sample values.

        Args:
            field: Field to generate preview for
            sample_values: Dict of dimension_name -> sample_value

        Returns:
            Preview string or error message
        """
        from ..services import NamingPatternValidator
        return NamingPatternValidator.get_naming_preview(self, field, sample_values)

    def get_required_dimensions(self, field):
        """Get list of dimensions required for the given field."""
        return self.rule_details.filter(field=field).values_list('dimension__name', flat=True)

    def get_fields_with_rules(self):
        """Get all fields that have rule details configured."""
        return self.rule_details.values_list('field', flat=True).distinct()

    def can_generate_for_field(self, field):
        """Check if this rule can generate strings for the given field."""
        return self.rule_details.filter(field=field).exists()

    def get_generation_order(self, field):
        """Get the dimension generation order for a specific field."""
        return list(
            self.rule_details.filter(field=field)
            .order_by('dimension_order')
            .values_list('dimension__name', flat=True)
        )

    def generate_string(self, field, dimension_values):
        """
        Generate a string value using this rule.

        Args:
            field: Field to generate for
            dimension_values: Dict mapping dimension names to values

        Returns:
            Generated string value

        Raises:
            ValidationError: If generation fails
        """
        from ..services import StringGenerationService

        try:
            return StringGenerationService.generate_string_value(
                self, field, dimension_values
            )
        except Exception as e:
            raise ValidationError(f"String generation failed: {str(e)}")

    @classmethod
    def get_default_for_platform(cls, platform):
        """Get the default rule for a platform within current workspace."""
        return cls.objects.filter(platform=platform, is_default=True).first()

    def get_absolute_url(self):
        return reverse("master_data_Rule_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Rule_update", args=(self.pk,))


class RuleDetailQuerySet(models.QuerySet):
    """Custom QuerySet for RuleDetail model."""

    def for_field(self, field):
        """Filter rule details for a specific field."""
        return self.filter(field=field)

    def ordered_by_dimension(self):
        """Order rule details by dimension order."""
        return self.order_by('dimension_order')


class RuleDetailManager(models.Manager):
    """Custom manager for RuleDetail model."""

    def get_queryset(self):
        from .base import get_current_workspace, _thread_locals
        queryset = RuleDetailQuerySet(self.model, using=self._db)
        # Auto-filter by workspace if context is set and user is not superuser
        current_workspace = get_current_workspace()
        if current_workspace and not getattr(_thread_locals, 'is_superuser', False):
            queryset = queryset.filter(workspace_id=current_workspace)
        return queryset

    def all_workspaces(self):
        """Get queryset without workspace filtering (for superusers)"""
        return RuleDetailQuerySet(self.model, using=self._db)

    def for_workspace(self, workspace_id):
        """Filter queryset by specific workspace"""
        return RuleDetailQuerySet(self.model, using=self._db).filter(workspace_id=workspace_id)

    def for_field(self, field):
        return self.get_queryset().for_field(field)


class RuleDetail(TimeStampModel, WorkspaceMixin):
    """
    Represents detailed configuration for how a rule formats dimension values.

    Defines the specific formatting (prefix, suffix, delimiter) and ordering
    for each dimension within a field's naming pattern.
    """

    # Relationships
    rule = models.ForeignKey(
        "master_data.Rule",
        on_delete=models.CASCADE,
        related_name="rule_details",
        help_text="Rule this detail belongs to"
    )
    field = models.ForeignKey(
        "master_data.Field",
        on_delete=models.CASCADE,
        related_name="rule_details",
        help_text="Field this formatting applies to"
    )
    dimension = models.ForeignKey(
        "master_data.Dimension",
        on_delete=models.CASCADE,
        related_name="rule_details",
        help_text="Dimension this formatting applies to"
    )

    # Fields
    prefix = models.CharField(
        max_length=PREFIX_SUFFIX_LENGTH,
        null=True,
        blank=True,
        help_text="Text to prepend to the dimension value"
    )
    suffix = models.CharField(
        max_length=PREFIX_SUFFIX_LENGTH,
        null=True,
        blank=True,
        help_text="Text to append to the dimension value"
    )
    delimiter = models.CharField(
        max_length=DELIMITER_LENGTH,
        null=True,
        blank=True,
        default='-',
        help_text="Character to separate this dimension from others"
    )
    dimension_order = models.SmallIntegerField(
        help_text="Order of this dimension in the naming sequence (1, 2, 3, etc.)"
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this dimension is required for string generation"
    )

    # Custom manager
    objects = RuleDetailManager()

    class Meta:
        verbose_name = "Rule Detail"
        verbose_name_plural = "Rule Details"
        # Unique per workspace
        unique_together = [("workspace", "rule", "field",
                            "dimension", 'dimension_order')]
        ordering = ['workspace', 'rule', 'field', 'dimension_order']
        indexes = [
            models.Index(fields=['workspace', 'rule', 'field']),
            models.Index(fields=['workspace', 'dimension']),
        ]

    def clean(self):
        """Validate rule detail configuration."""
        super().clean()

        # Validate dimension order uniqueness within rule+field per workspace
        if self.dimension_order is not None:
            existing_order = RuleDetail.objects.filter(
                workspace=self.workspace,
                rule=self.rule,
                field=self.field,
                dimension_order=self.dimension_order
            ).exclude(pk=self.pk)

            if existing_order.exists():
                raise ValidationError(
                    f"Dimension order {self.dimension_order} is already used for "
                    f"field '{self.field.name}' in rule '{self.rule.name}' in this workspace"
                )

        # Validate that rule and dimension belong to the same workspace
        if self.rule and self.rule.workspace != self.workspace:
            raise ValidationError("Rule must belong to the same workspace")
        if self.dimension and self.dimension.workspace != self.workspace:
            raise ValidationError(
                "Dimension must belong to the same workspace")

    def format_value(self, value):
        """
        Format a dimension value according to this rule detail's configuration.

        Args:
            value: The raw dimension value to format

        Returns:
            Formatted value with prefix/suffix applied
        """
        if value is None:
            return ""

        formatted = str(value)

        if self.prefix:
            formatted = self.prefix + formatted

        if self.suffix:
            formatted = formatted + self.suffix

        return formatted

    def get_effective_delimiter(self):
        """Get the effective delimiter (default to '-' if None)."""
        return self.delimiter if self.delimiter is not None else '-'

    def __str__(self):
        order_info = f" (Order: {self.dimension_order})" if self.dimension_order else ""
        return (
            f"{self.rule.name} - {self.field.name} - "
            f"{self.dimension.name}{order_info}"
        )

    def get_absolute_url(self):
        return reverse("master_data_RuleDetail_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_RuleDetail_update", args=(self.pk,))
