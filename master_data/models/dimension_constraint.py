"""
Dimension Constraint models for the master_data app.
"""

from django.db import models
from django.core.exceptions import ValidationError

from .base import TimeStampModel, WorkspaceMixin
from ..constants import STANDARD_NAME_LENGTH


class ConstraintTypeChoices(models.TextChoices):
    """Constraint types supported for dimension values."""
    NO_SPACES = 'no_spaces', 'No Spaces'
    LOWERCASE = 'lowercase', 'Lowercase Only'
    UPPERCASE = 'uppercase', 'Uppercase Only'
    NO_SPECIAL_CHARS = 'no_special_chars', 'No Special Characters'
    ALPHANUMERIC = 'alphanumeric', 'Alphanumeric Only'
    NUMERIC = 'numeric', 'Numeric Only'
    MAX_LENGTH = 'max_length', 'Maximum Length'
    MIN_LENGTH = 'min_length', 'Minimum Length'
    REGEX = 'regex', 'Regular Expression'
    STARTS_WITH = 'starts_with', 'Starts With'
    ENDS_WITH = 'ends_with', 'Ends With'
    ALLOWED_CHARS = 'allowed_chars', 'Allowed Characters'
    NO_UPPERCASE = 'no_uppercase', 'No Uppercase'
    NO_NUMBERS = 'no_numbers', 'No Numbers'
    URL_SAFE = 'url_safe', 'URL Safe'


# Constraint types that require a configuration value
CONSTRAINT_TYPES_REQUIRING_VALUE = {
    ConstraintTypeChoices.MAX_LENGTH,
    ConstraintTypeChoices.MIN_LENGTH,
    ConstraintTypeChoices.REGEX,
    ConstraintTypeChoices.STARTS_WITH,
    ConstraintTypeChoices.ENDS_WITH,
    ConstraintTypeChoices.ALLOWED_CHARS,
}


class DimensionConstraint(TimeStampModel):
    """
    Represents a validation constraint for dimension values.

    Constraints define rules that dimension values must satisfy
    (e.g., lowercase only, maximum length, no spaces).
    """

    # Relationships
    dimension = models.ForeignKey(
        "master_data.Dimension",
        on_delete=models.CASCADE,
        related_name="constraints",
        help_text="The dimension this constraint applies to"
    )

    # Fields
    constraint_type = models.CharField(
        max_length=STANDARD_NAME_LENGTH,
        choices=ConstraintTypeChoices.choices,
        help_text="Type of constraint to apply"
    )
    value = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Configuration value for constraints that need it (e.g., max_length, regex pattern)"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Custom error message to display when constraint is violated"
    )
    order = models.IntegerField(
        default=0,
        help_text="Order in which constraint is applied (lower numbers first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this constraint is currently active"
    )

    class Meta:
        verbose_name = "Dimension Constraint"
        verbose_name_plural = "Dimension Constraints"
        ordering = ['dimension', 'order']
        unique_together = [
            ('dimension', 'order'),  # Order unique per dimension
        ]
        indexes = [
            models.Index(fields=['dimension']),
            models.Index(fields=['dimension', 'is_active']),
        ]

    def __str__(self):
        return f"{self.dimension.name}: {self.get_constraint_type_display()} (order: {self.order})"

    def clean(self):
        """Validate the constraint configuration."""
        super().clean()

        # Validate that required value is provided for certain constraint types
        if self.constraint_type in CONSTRAINT_TYPES_REQUIRING_VALUE:
            if not self.value:
                raise ValidationError({
                    'value': f"Constraint type '{self.constraint_type}' requires a configuration value"
                })

        # Validate specific constraint types
        if self.constraint_type == ConstraintTypeChoices.MAX_LENGTH:
            try:
                max_val = int(self.value)
                if max_val <= 0:
                    raise ValidationError({'value': 'Maximum length must be positive'})
            except (ValueError, TypeError):
                raise ValidationError({'value': 'Maximum length must be a valid integer'})

        elif self.constraint_type == ConstraintTypeChoices.MIN_LENGTH:
            try:
                min_val = int(self.value)
                if min_val < 0:
                    raise ValidationError({'value': 'Minimum length must be non-negative'})
            except (ValueError, TypeError):
                raise ValidationError({'value': 'Minimum length must be a valid integer'})

        elif self.constraint_type == ConstraintTypeChoices.REGEX:
            # Validate regex pattern to prevent ReDoS attacks
            import re
            try:
                re.compile(self.value)
            except re.error as e:
                raise ValidationError({'value': f'Invalid regex pattern: {str(e)}'})

            # Basic ReDoS prevention: check for dangerous patterns
            if self.value:
                dangerous_patterns = [
                    r'(\w+)*',  # Nested quantifiers
                    r'(\w*)*',
                    r'(\w+)+',
                    r'(\w*)+',
                ]
                for pattern in dangerous_patterns:
                    if pattern in self.value:
                        raise ValidationError({
                            'value': 'Regex pattern may cause performance issues (nested quantifiers)'
                        })

    def save(self, *args, **kwargs):
        """Override save to auto-calculate order if not provided."""
        if self.order == 0 and not self.pk:
            # Auto-assign order as max(order) + 1 for this dimension
            max_order = DimensionConstraint.objects.filter(
                dimension=self.dimension
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1

        self.full_clean()
        super().save(*args, **kwargs)

    def get_default_error_message(self):
        """Get the default error message for this constraint type."""
        default_messages = {
            ConstraintTypeChoices.NO_SPACES: "No whitespace allowed",
            ConstraintTypeChoices.LOWERCASE: "Only lowercase letters allowed",
            ConstraintTypeChoices.UPPERCASE: "Only uppercase letters allowed",
            ConstraintTypeChoices.NO_SPECIAL_CHARS: "Only letters, numbers, and underscores allowed",
            ConstraintTypeChoices.ALPHANUMERIC: "Only letters and numbers allowed",
            ConstraintTypeChoices.NUMERIC: "Only numbers allowed",
            ConstraintTypeChoices.MAX_LENGTH: f"Maximum length is {self.value} characters",
            ConstraintTypeChoices.MIN_LENGTH: f"Minimum length is {self.value} characters",
            ConstraintTypeChoices.REGEX: f"Value must match pattern: {self.value}",
            ConstraintTypeChoices.STARTS_WITH: f"Value must start with '{self.value}'",
            ConstraintTypeChoices.ENDS_WITH: f"Value must end with '{self.value}'",
            ConstraintTypeChoices.ALLOWED_CHARS: "Value contains disallowed characters",
            ConstraintTypeChoices.NO_UPPERCASE: "Uppercase letters are not allowed",
            ConstraintTypeChoices.NO_NUMBERS: "Numbers are not allowed",
            ConstraintTypeChoices.URL_SAFE: "Only URL-safe characters allowed (a-z, A-Z, 0-9, -, _, .)",
        }
        return default_messages.get(self.constraint_type, "Constraint validation failed")
