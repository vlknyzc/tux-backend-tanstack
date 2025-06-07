from django.urls import path, include
from rest_framework import routers

from .views import (
    DimensionViewSet,
    DimensionValueViewSet,
    WorkspaceViewSet,
    PlatformViewSet,
    FieldViewSet,
    RuleViewSet,
    RuleDetailViewSet,
    RuleNestedViewSet,
    SubmissionViewSet,
    StringViewSet,
    StringDetailViewSet,
    SubmissionNestedViewSet,
    # Rule configuration views
    LightweightRuleView,
    FieldSpecificRuleView,
    RuleValidationView,
    GenerationPreviewView,
    CacheManagementView,
    RuleConfigurationView,
)

router = routers.DefaultRouter()
router.register("dimensions", DimensionViewSet)
router.register("dimension-values", DimensionValueViewSet)
router.register("workspaces", WorkspaceViewSet)
router.register("platforms", PlatformViewSet)
router.register("fields", FieldViewSet)
router.register("rules", RuleViewSet)
router.register("rule-details", RuleDetailViewSet)
router.register("rule-nested", RuleNestedViewSet, basename="rule-nested")

router.register("submissions", SubmissionViewSet)
router.register("strings", StringViewSet)
router.register("string-details", StringDetailViewSet)
router.register("nested-submissions", SubmissionNestedViewSet,
                basename="nested-submissions")

urlpatterns = [
    path("", include(router.urls)),

    # Rule configuration endpoint
    path("rules/<int:rule_id>/configuration/",
         RuleConfigurationView.as_view(),
         name="rule-configuration"),

    # Additional rule endpoints
    path("rules/<int:rule_id>/lightweight/",
         LightweightRuleView.as_view(),
         name="rule-lightweight"),

    path("rules/<int:rule_id>/fields/<int:field_id>/",
         FieldSpecificRuleView.as_view(),
         name="rule-field-specific"),

    path("rules/<int:rule_id>/validation/",
         RuleValidationView.as_view(),
         name="rule-validation"),

    path("rules/generation-preview/",
         GenerationPreviewView.as_view(),
         name="rule-generation-preview"),

    # Cache management endpoints
    path("rules/cache/invalidate/",
         CacheManagementView.as_view(),
         name="rule-cache-invalidate"),

    path("rules/<int:rule_id>/metrics/",
         CacheManagementView.as_view(),
         name="rule-performance-metrics"),
]
