"""
RuleMetricsService: Calculates performance metrics for rules.

This service handles performance and quality metric calculations for rules,
including:
- Completeness scoring
- Inheritance coverage
- Field analysis metrics
- Performance estimates

Part of the refactoring from God Class (Issue #13) to separate metrics
calculation from business logic.
"""

from typing import Dict, List
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class RuleMetricsService:
    """
    Service for calculating rule performance and quality metrics.

    Responsibilities:
    - Performance metrics calculation
    - Completeness score computation
    - Inheritance coverage analysis
    - Field-level statistics
    - Generation time estimates

    This service focuses solely on metrics calculation, separated from
    validation, caching, and other concerns.
    """

    def __init__(self):
        """Initialize metrics service."""
        pass

    def calculate_performance_metrics(
        self,
        field_templates: List[Dict],
        dimension_catalog: Dict
    ) -> Dict:
        """
        Calculate comprehensive performance metrics for rule data.

        Analyzes field templates and dimension catalog to compute:
        - Total dimensions and fields
        - Average completeness scores
        - Inheritance coverage
        - Fields analyzed count
        - Generation timestamp

        Args:
            field_templates: List of field templates from FieldTemplateService
            dimension_catalog: Dictionary containing dimension catalog data
                from DimensionCatalogService

        Returns:
            Dictionary containing:
            - total_dimensions: Number of dimensions in catalog
            - total_fields: Number of field templates
            - average_completeness_score: Average completeness across all fields
            - inheritance_coverage: Percentage of dimensions with inheritance
            - fields_analyzed: Number of fields with completeness scores
            - timestamp: ISO format timestamp of calculation
        """
        total_dimensions = len(dimension_catalog.get('dimensions', {}))
        total_fields = len(field_templates)

        # Calculate completeness scores
        field_completeness_scores = []
        for template in field_templates:
            if template.get('dimensions'):
                required_dims = sum(
                    1 for d in template['dimensions']
                    if d.get('is_required', False)
                )
                total_dims = len(template['dimensions'])
                score = (
                    (required_dims / total_dims) * 100
                    if total_dims > 0 else 0
                )
                field_completeness_scores.append(score)

        avg_completeness = (
            sum(field_completeness_scores) / len(field_completeness_scores)
            if field_completeness_scores else 0
        )

        # Get inheritance stats
        inheritance_stats = dimension_catalog.get(
            'inheritance_lookup', {}
        ).get('inheritance_stats', {})
        inheritance_coverage = inheritance_stats.get(
            'inheritance_coverage', 0.0
        )

        return {
            'total_dimensions': total_dimensions,
            'total_fields': total_fields,
            'average_completeness_score': round(avg_completeness, 2),
            'inheritance_coverage': round(inheritance_coverage * 100, 2),
            'fields_analyzed': len(field_completeness_scores),
            'timestamp': timezone.now().isoformat()
        }

    def calculate_completeness_scores(
        self,
        field_templates: List[Dict]
    ) -> List[float]:
        """
        Calculate completeness scores for all field templates.

        Completeness score measures how many required dimensions
        are configured out of total dimensions for each field.

        Args:
            field_templates: List of field templates

        Returns:
            List of completeness scores (0-100) for each field
        """
        completeness_scores = []

        for template in field_templates:
            if template.get('dimensions'):
                required_dims = sum(
                    1 for d in template['dimensions']
                    if d.get('is_required', False)
                )
                total_dims = len(template['dimensions'])
                score = (
                    (required_dims / total_dims) * 100
                    if total_dims > 0 else 0
                )
                completeness_scores.append(score)
            else:
                completeness_scores.append(0.0)

        return completeness_scores

    def calculate_inheritance_coverage(
        self,
        dimension_catalog: Dict
    ) -> float:
        """
        Calculate inheritance coverage from dimension catalog.

        Inheritance coverage measures what percentage of dimensions
        have parent-child inheritance relationships configured.

        Args:
            dimension_catalog: Dimension catalog from DimensionCatalogService

        Returns:
            Inheritance coverage as percentage (0.0-100.0)
        """
        inheritance_stats = dimension_catalog.get(
            'inheritance_lookup', {}
        ).get('inheritance_stats', {})

        coverage = inheritance_stats.get('inheritance_coverage', 0.0)
        return round(coverage * 100, 2)

    def estimate_generation_time(
        self,
        field_templates: List[Dict],
        dimension_catalog: Dict
    ) -> float:
        """
        Estimate string generation time based on rule complexity.

        Time estimate considers:
        - Number of dimensions
        - Number of fields
        - Inheritance relationships
        - Dimension values count

        Args:
            field_templates: List of field templates
            dimension_catalog: Dimension catalog data

        Returns:
            Estimated generation time in milliseconds
        """
        total_dimensions = len(dimension_catalog.get('dimensions', {}))
        total_fields = len(field_templates)

        # Base time per field (ms)
        base_time = 10

        # Additional time per dimension (ms)
        dimension_time = total_dimensions * 2

        # Additional time for inheritance processing (ms)
        inheritance_time = 0
        inheritance_stats = dimension_catalog.get(
            'inheritance_lookup', {}
        ).get('inheritance_stats', {})
        if inheritance_stats.get('has_inheritance', False):
            inheritance_time = 20

        # Calculate total estimate
        estimated_time = (base_time * total_fields) + dimension_time + inheritance_time

        return round(estimated_time, 2)

    def get_field_statistics(
        self,
        field_templates: List[Dict]
    ) -> Dict:
        """
        Get detailed statistics about fields.

        Args:
            field_templates: List of field templates

        Returns:
            Dictionary with field statistics:
            - total_fields: Total number of fields
            - fields_with_dimensions: Fields that have dimensions configured
            - fields_can_generate: Fields that can generate strings
            - average_dimensions_per_field: Average dimension count
            - min_dimensions: Minimum dimensions in any field
            - max_dimensions: Maximum dimensions in any field
        """
        if not field_templates:
            return {
                'total_fields': 0,
                'fields_with_dimensions': 0,
                'fields_can_generate': 0,
                'average_dimensions_per_field': 0,
                'min_dimensions': 0,
                'max_dimensions': 0
            }

        dimension_counts = [
            len(template.get('dimensions', []))
            for template in field_templates
        ]

        return {
            'total_fields': len(field_templates),
            'fields_with_dimensions': sum(1 for count in dimension_counts if count > 0),
            'fields_can_generate': sum(
                1 for template in field_templates
                if template.get('can_generate', False)
            ),
            'average_dimensions_per_field': round(
                sum(dimension_counts) / len(dimension_counts), 2
            ) if dimension_counts else 0,
            'min_dimensions': min(dimension_counts) if dimension_counts else 0,
            'max_dimensions': max(dimension_counts) if dimension_counts else 0
        }

    def get_dimension_statistics(
        self,
        dimension_catalog: Dict
    ) -> Dict:
        """
        Get detailed statistics about dimensions.

        Args:
            dimension_catalog: Dimension catalog data

        Returns:
            Dictionary with dimension statistics:
            - total_dimensions: Total number of dimensions
            - dimensions_with_values: Dimensions that have values configured
            - total_dimension_values: Total count of all dimension values
            - average_values_per_dimension: Average values per dimension
            - dimensions_with_inheritance: Count of dimensions with parent-child relationships
        """
        dimensions = dimension_catalog.get('dimensions', {})
        dimension_values = dimension_catalog.get('dimension_values', {})

        total_dimensions = len(dimensions)
        dimensions_with_values = len(dimension_values)

        # Count total dimension values
        total_values = sum(
            len(values) for values in dimension_values.values()
        )

        # Count dimensions with inheritance
        dimensions_with_inheritance = 0
        for dim_id, dim_data in dimensions.items():
            if dim_data.get('parent') or dim_data.get('has_children', False):
                dimensions_with_inheritance += 1

        return {
            'total_dimensions': total_dimensions,
            'dimensions_with_values': dimensions_with_values,
            'total_dimension_values': total_values,
            'average_values_per_dimension': round(
                total_values / dimensions_with_values, 2
            ) if dimensions_with_values > 0 else 0,
            'dimensions_with_inheritance': dimensions_with_inheritance
        }
