"""
Rule serializers public API.

This module exports all rule-related serializers from their organized
submodules while maintaining backward compatibility with existing imports.

All serializers are organized into focused modules by responsibility:
- base.py: Write/create/update serializers
- read.py: Read/display serializers
- validation.py: Validation serializers
- request.py: API request serializers
- response.py: API response serializers
- catalog.py: Catalog and configuration serializers
- dimension_ref.py: Dimension reference serializers
- field_template.py: Field template serializers
- metadata.py: Metadata and inheritance serializers
"""

# =============================================================================
# WRITE SERIALIZERS (for creating/updating data)
# =============================================================================

from .base import (
    RuleDetailCreateSerializer,
    RuleCreateUpdateSerializer,
    RuleNestedSerializer,
)

# =============================================================================
# READ SERIALIZERS (for displaying/retrieving data)
# =============================================================================

from .read import (
    RuleDetailReadSerializer,
    RuleReadSerializer,
    RuleNestedReadSerializer,
)

# =============================================================================
# VALIDATION SERIALIZERS
# =============================================================================

from .validation import (
    RuleValidationSerializer,
)

# =============================================================================
# REQUEST SERIALIZERS (for API interactions)
# =============================================================================

from .request import (
    RulePreviewRequestSerializer,
    DefaultRuleRequestSerializer,
    GenerationPreviewRequestSerializer,
    CacheInvalidationRequestSerializer,
)

# =============================================================================
# RESPONSE SERIALIZERS (for API responses)
# =============================================================================

from .response import (
    APIVersionResponseSerializer,
    APIHealthResponseSerializer,
    VersionDemoResponseSerializer,
    ErrorResponseSerializer,
    CacheInvalidationResponseSerializer,
    GenerationPreviewResponseSerializer,
)

# =============================================================================
# CATALOG SERIALIZERS
# =============================================================================

from .catalog import (
    LightweightRuleSerializer,
    OptimizedDimensionCatalogSerializer,
    RuleConfigurationSerializer,
    DimensionRelationshipMapsSerializer,
    EnhancedDimensionCatalogSerializer,
    CompleteRuleSerializer,
    DimensionCatalogSerializer,
)

# =============================================================================
# DIMENSION REFERENCE SERIALIZERS
# =============================================================================

from .dimension_ref import (
    DimensionDefinitionSerializer,
    DimensionValueSerializer,
    DimensionReferenceSerializer,
)

# =============================================================================
# FIELD TEMPLATE SERIALIZERS
# =============================================================================

from .field_template import (
    OptimizedEntityTemplateSerializer,
    EntityDimensionSerializer,
    EntityTemplateSerializer,
    EntitySpecificDataSerializer,
)

# =============================================================================
# METADATA SERIALIZERS
# =============================================================================

from .metadata import (
    InheritanceLookupSerializer,
    ConstraintRelationshipSerializer,
    ValidationRuleSerializer,
    GenerationMetadataSerializer,
    InheritanceInfoSerializer,
    ConstraintLookupSerializer,
    MetadataIndexesSerializer,
    ValidationSummarySerializer,
    PerformanceMetricsSerializer,
    GenerationPreviewSerializer,
)

# =============================================================================
# PUBLIC API (all exported serializers)
# =============================================================================

__all__ = [
    # Write serializers
    'RuleDetailCreateSerializer',
    'RuleCreateUpdateSerializer',
    'RuleNestedSerializer',

    # Read serializers
    'RuleDetailReadSerializer',
    'RuleReadSerializer',
    'RuleNestedReadSerializer',

    # Validation serializers
    'RuleValidationSerializer',

    # Request serializers
    'RulePreviewRequestSerializer',
    'DefaultRuleRequestSerializer',
    'GenerationPreviewRequestSerializer',
    'CacheInvalidationRequestSerializer',

    # Response serializers
    'APIVersionResponseSerializer',
    'APIHealthResponseSerializer',
    'VersionDemoResponseSerializer',
    'ErrorResponseSerializer',
    'CacheInvalidationResponseSerializer',
    'GenerationPreviewResponseSerializer',

    # Catalog serializers
    'LightweightRuleSerializer',
    'OptimizedDimensionCatalogSerializer',
    'RuleConfigurationSerializer',
    'DimensionRelationshipMapsSerializer',
    'EnhancedDimensionCatalogSerializer',
    'CompleteRuleSerializer',
    'DimensionCatalogSerializer',

    # Dimension reference serializers
    'DimensionDefinitionSerializer',
    'DimensionValueSerializer',
    'DimensionReferenceSerializer',

    # Field template serializers
    'OptimizedEntityTemplateSerializer',
    'EntityDimensionSerializer',
    'EntityTemplateSerializer',
    'EntitySpecificDataSerializer',

    # Metadata serializers
    'InheritanceLookupSerializer',
    'ConstraintRelationshipSerializer',
    'ValidationRuleSerializer',
    'GenerationMetadataSerializer',
    'InheritanceInfoSerializer',
    'ConstraintLookupSerializer',
    'MetadataIndexesSerializer',
    'ValidationSummarySerializer',
    'PerformanceMetricsSerializer',
    'GenerationPreviewSerializer',
]
