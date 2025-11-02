from .dimension import (
    DimensionSerializer,
    DimensionValueSerializer,
    DimensionBulkCreateSerializer,
    DimensionValueBulkCreateSerializer
)
from .dimension_constraint import (
    DimensionConstraintSerializer,
    ConstraintBulkCreateSerializer,
    ConstraintReorderSerializer,
    DimensionValueValidationSerializer,
)
from .rule import (
    # Core serializers
    RuleReadSerializer,
    RuleDetailReadSerializer,
    RuleNestedSerializer,
    RuleNestedReadSerializer,
    RulePreviewRequestSerializer,
    RuleValidationSerializer,
    RuleDetailCreateSerializer,
    DefaultRuleRequestSerializer,

    # Extended catalog serializers
    FieldTemplateSerializer,
    FieldSpecificDataSerializer,
    LightweightRuleSerializer,
    DimensionCatalogSerializer,
    GenerationPreviewSerializer,
    ValidationSummarySerializer,
    GenerationPreviewRequestSerializer,
    CacheInvalidationRequestSerializer,
    InheritanceLookupSerializer,
    DimensionRelationshipMapsSerializer,
    ConstraintLookupSerializer,
    MetadataIndexesSerializer,
    EnhancedDimensionCatalogSerializer,
    PerformanceMetricsSerializer,
    CompleteRuleSerializer,
    RuleConfigurationSerializer,

    # API response serializers
    APIVersionResponseSerializer,
    APIHealthResponseSerializer,
    VersionDemoResponseSerializer,
    ErrorResponseSerializer,
    CacheInvalidationResponseSerializer,
    GenerationPreviewResponseSerializer,
)
from .platform import PlatformSerializer, FieldSerializer, PlatformTemplateSerializer
from .string import (
    StringDetailNestedSerializer,
    StringWithDetailsSerializer,
    StringWithDetailsReadSerializer,
    StringDetailExpandedSerializer,
    StringDetailReadSerializer,
    StringDetailWriteSerializer,
    WorkspaceValidationMixin,
)
from .workspace import WorkspaceSerializer
# from .submission import (  # DEPRECATED: Use Projects instead
#     SubmissionWithStringsSerializer,
#     SubmissionWithStringsReadSerializer,
# )
from .batch_operations import (
    StringBatchUpdateRequestSerializer,
    StringBatchUpdateResponseSerializer,
    InheritanceImpactRequestSerializer,
    InheritanceImpactResponseSerializer,
    StringHistoryResponseSerializer,
    RollbackRequestSerializer,
    RollbackResponseSerializer,
    StringModificationSerializer,
    StringUpdateBatchSerializer,
    StringInheritanceUpdateSerializer,
)
from .propagation import (
    PropagationImpactRequestSerializer,
    PropagationImpactResponseSerializer,
    StringDetailUpdateWithPropagationSerializer,
    PropagationJobSerializer,
    PropagationErrorSerializer,
    StringDetailBatchUpdateRequestSerializer,
    StringDetailBatchUpdateResponseSerializer,
    PropagationSettingsSerializer,
)
from .bulk_operations import (
    BulkStringCreateSerializer,
    BulkStringDetailUpdateSerializer,
    # BulkSubmissionCreateSerializer,  # DEPRECATED
    BulkStringDeleteSerializer,
    BulkValidationResultSerializer,
    BulkOperationStatusSerializer,
)
from .project import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    ProjectMemberReadSerializer,
    ProjectMemberWriteSerializer,
    ProjectActivitySerializer,
    ApprovalHistorySerializer,
    SubmitForApprovalSerializer,
    ApproveSerializer,
    RejectSerializer,
)
from .project_string import (
    ProjectStringReadSerializer,
    ProjectStringExpandedSerializer,
    ProjectStringWriteSerializer,
    BulkProjectStringCreateSerializer,
    ProjectStringUpdateSerializer,
    ProjectStringDetailNestedSerializer,
    ProjectStringDetailWriteSerializer,
    ListProjectStringsSerializer,
)


__all__ = [
    'DimensionSerializer',
    'DimensionValueSerializer',
    'DimensionBulkCreateSerializer',
    'DimensionValueBulkCreateSerializer',
    'DimensionConstraintSerializer',
    'ConstraintBulkCreateSerializer',
    'ConstraintReorderSerializer',
    'DimensionValueValidationSerializer',
    'RuleReadSerializer',
    'RuleDetailReadSerializer',
    'RuleNestedSerializer',
    'RuleNestedReadSerializer',
    'RulePreviewRequestSerializer',
    'RuleValidationSerializer',
    'RuleDetailCreateSerializer',
    'DefaultRuleRequestSerializer',
    # Enhanced rule serializers
    'LightweightRuleSerializer',
    'FieldTemplateSerializer',
    'FieldSpecificDataSerializer',
    'DimensionCatalogSerializer',
    'GenerationPreviewSerializer',
    'ValidationSummarySerializer',
    'GenerationPreviewRequestSerializer',
    'CacheInvalidationRequestSerializer',
    'InheritanceLookupSerializer',
    'DimensionRelationshipMapsSerializer',
    'ConstraintLookupSerializer',
    'MetadataIndexesSerializer',
    'EnhancedDimensionCatalogSerializer',
    'PerformanceMetricsSerializer',
    'CompleteRuleSerializer',
    'RuleConfigurationSerializer',

    # API response serializers
    'APIVersionResponseSerializer',
    'APIHealthResponseSerializer',
    'VersionDemoResponseSerializer',
    'ErrorResponseSerializer',
    'CacheInvalidationResponseSerializer',
    'GenerationPreviewResponseSerializer',
    'PlatformSerializer',
    'FieldSerializer',
    'PlatformTemplateSerializer',
    'StringExpandedSerializer',
    'StringGenerationRequestSerializer',
    'StringRegenerationSerializer',
    'StringConflictCheckSerializer',
    'StringBulkGenerationRequestSerializer',
    'WorkspaceSerializer',
    # Batch operations serializers
    'StringBatchUpdateRequestSerializer',
    'StringBatchUpdateResponseSerializer',
    'InheritanceImpactRequestSerializer',
    'InheritanceImpactResponseSerializer',
    'StringHistoryResponseSerializer',
    'RollbackRequestSerializer',
    'RollbackResponseSerializer',
    'StringModificationSerializer',
    'StringUpdateBatchSerializer',
    'StringInheritanceUpdateSerializer',
    # Propagation serializers
    'PropagationImpactRequestSerializer',
    'PropagationImpactResponseSerializer',
    'StringDetailUpdateWithPropagationSerializer',
    'PropagationJobSerializer',
    'PropagationErrorSerializer',
    'StringDetailUpdateItemSerializer',
    'StringDetailBatchUpdateRequestSerializer',
    'StringDetailBatchUpdateResponseSerializer',
    'PropagationSettingsSerializer',

    # New main_api serializers
    'StringDetailNestedSerializer',
    'StringWithDetailsSerializer',
    'StringWithDetailsReadSerializer',
    'StringDetailExpandedSerializer',
    'StringDetailReadSerializer',
    'StringDetailWriteSerializer',
    'WorkspaceValidationMixin',
    # 'SubmissionWithStringsSerializer',  # DEPRECATED
    # 'SubmissionWithStringsReadSerializer',  # DEPRECATED

    # Bulk operations
    'BulkStringCreateSerializer',
    'BulkStringDetailUpdateSerializer',
    # 'BulkSubmissionCreateSerializer',  # DEPRECATED
    'BulkStringDeleteSerializer',
    'BulkValidationResultSerializer',
    'BulkOperationStatusSerializer',

    # Project serializers
    'ProjectListSerializer',
    'ProjectDetailSerializer',
    'ProjectCreateSerializer',
    'ProjectUpdateSerializer',
    'ProjectMemberReadSerializer',
    'ProjectMemberWriteSerializer',
    'ProjectActivitySerializer',
    'ApprovalHistorySerializer',
    'SubmitForApprovalSerializer',
    'ApproveSerializer',
    'RejectSerializer',

    # Project string serializers
    'ProjectStringReadSerializer',
    'ProjectStringExpandedSerializer',
    'ProjectStringWriteSerializer',
    'BulkProjectStringCreateSerializer',
    'ProjectStringUpdateSerializer',
    'ProjectStringDetailNestedSerializer',
    'ProjectStringDetailWriteSerializer',
    'ListProjectStringsSerializer',
]
