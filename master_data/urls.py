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
    # Version views
    APIVersionView,
    APIHealthView,
    VersionDemoView,
)

router = routers.DefaultRouter()
router.register("dimensions", DimensionViewSet, basename="dimension")
router.register("dimension-values", DimensionValueViewSet,
                basename="dimensionvalue")
router.register("workspaces", WorkspaceViewSet, basename="workspace")
router.register("platforms", PlatformViewSet, basename="platform")
router.register("fields", FieldViewSet, basename="field")
router.register("rules", RuleViewSet, basename="rule")
router.register("rule-details", RuleDetailViewSet, basename="ruledetail")
router.register("rule-nested", RuleNestedViewSet, basename="rule-nested")

router.register("submissions", SubmissionViewSet, basename="submission")
router.register("strings", StringViewSet, basename="string")
router.register("string-details", StringDetailViewSet, basename="stringdetail")
router.register("nested-submissions", SubmissionNestedViewSet,
                basename="nested-submissions")

urlpatterns = [
    path("", include(router.urls)),

    # API version and health endpoints
    path("version/", APIVersionView.as_view(), name="api-version"),
    path("health/", APIHealthView.as_view(), name="api-health"),
    path("demo/", VersionDemoView.as_view(), name="api-version-demo"),

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
