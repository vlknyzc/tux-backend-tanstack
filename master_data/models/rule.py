"""
Rule models for the master_data app.
Handles naming convention rules and their detailed configurations.
"""

from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

from .base import TimeStampModel
from ..constants import (
    LONG_NAME_LENGTH, DESCRIPTION_LENGTH, PREFIX_SUFFIX_LENGTH,
    DELIMITER_LENGTH, STANDARD_NAME_LENGTH, StatusChoices
)


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
        return RuleQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def for_platform(self, platform):
        return self.get_queryset().for_platform(platform)


class Rule(TimeStampModel):
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
    objects = RuleManager()

    class Meta:
        verbose_name = "Rule"
        verbose_name_plural = "Rules"
        unique_together = ('platform', 'name')
        ordering = ['platform', 'name']
        indexes = [
            models.Index(fields=['platform', 'status']),
            models.Index(fields=['is_default']),
        ]

    def clean(self):
        """Validate rule configuration."""
        super().clean()

        # Ensure only one default rule per platform
        if self.is_default:
            existing_default = Rule.objects.filter(
                platform=self.platform,
                is_default=True
            ).exclude(pk=self.pk)

            if existing_default.exists():
                raise ValidationError(
                    f"Platform '{self.platform.name}' already has a default rule: "
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
        """Get the default rule for a platform."""
        try:
            return cls.objects.get(platform=platform, is_default=True, status=StatusChoices.ACTIVE)
        except cls.DoesNotExist:
            return None

    def get_absolute_url(self):
        return reverse("master_data_Rule_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_Rule_update", args=(self.pk,))


class RuleDetailQuerySet(models.QuerySet):
    """Custom QuerySet for RuleDetail model."""

    def for_field(self, field):
        """Filter details for a specific field."""
        return self.filter(field=field)

    def ordered_by_dimension(self):
        """Order by dimension_order for proper sequence."""
        return self.order_by('dimension_order')


class RuleDetailManager(models.Manager):
    """Custom manager for RuleDetail model."""

    def get_queryset(self):
        return RuleDetailQuerySet(self.model, using=self._db)

    def for_field(self, field):
        return self.get_queryset().for_field(field)


class RuleDetail(TimeStampModel):
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
        unique_together = ("rule", "field", "dimension", 'dimension_order')
        ordering = ['rule', 'field', 'dimension_order']
        indexes = [
            models.Index(fields=['rule', 'field', 'dimension_order']),
        ]

    def clean(self):
        """Validate rule detail configuration."""
        super().clean()

        # Validate dimension_order is positive
        if self.dimension_order <= 0:
            raise ValidationError("Dimension order must be positive")

        # Validate rule and field belong to same platform
        if self.rule.platform != self.field.platform:
            raise ValidationError(
                "Rule and field must belong to the same platform")

        # Check for dimension_order gaps within the same rule+field
        existing_orders = RuleDetail.objects.filter(
            rule=self.rule,
            field=self.field
        ).exclude(pk=self.pk).values_list('dimension_order', flat=True)

        if existing_orders:
            all_orders = list(existing_orders) + [self.dimension_order]
            all_orders.sort()
            expected_orders = list(range(1, len(all_orders) + 1))

            if all_orders != expected_orders:
                raise ValidationError(
                    f"Dimension order {self.dimension_order} creates gaps. "
                    f"Expected sequence: {expected_orders}"
                )

    def format_value(self, value):
        """
        Format a dimension value according to this rule detail.

        Args:
            value: Raw dimension value

        Returns:
            Formatted value with prefix and suffix applied
        """
        formatted = str(value)
        if self.prefix:
            formatted = f"{self.prefix}{formatted}"
        if self.suffix:
            formatted = f"{formatted}{self.suffix}"
        return formatted

    def get_effective_delimiter(self):
        """Get the effective delimiter (using default if none specified)."""
        return self.delimiter or '-'

    def __str__(self):
        order_info = f"#{self.dimension_order}"
        formatting = []

        if self.prefix:
            formatting.append(f"prefix: '{self.prefix}'")
        if self.suffix:
            formatting.append(f"suffix: '{self.suffix}'")
        if self.delimiter:
            formatting.append(f"delimiter: '{self.delimiter}'")

        format_info = f" ({', '.join(formatting)})" if formatting else ""

        return f"{self.rule.name} - {self.field.name} - {self.dimension.name} {order_info}{format_info}"

    def get_absolute_url(self):
        return reverse("master_data_RuleDetail_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("master_data_RuleDetail_update", args=(self.pk,))
