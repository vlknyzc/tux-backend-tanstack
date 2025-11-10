from django.urls import path, include
from rest_framework import routers

from .views import (
    DimensionViewSet,
    DimensionValueViewSet,
    DimensionConstraintViewSet,
    WorkspaceViewSet,
    PlatformViewSet,
    EntityViewSet,
    RuleViewSet,
    RuleDetailViewSet,
    RuleNestedViewSet,
    # Rule configuration views
    LightweightRuleView,
    EntitySpecificRuleView,
    RuleValidationView,
    GenerationPreviewView,
    CacheManagementView,
    RuleConfigurationView,
    # Version views
    APIVersionView,
    APIHealthView,
    VersionDemoView,
    # Propagation views
    PropagationJobViewSet,
    PropagationErrorViewSet,
    EnhancedStringDetailViewSet,
    PropagationSettingsViewSet,
)

router = routers.DefaultRouter()

# Global resources (no workspace_id in path)
router.register("workspaces", WorkspaceViewSet, basename="workspace")
router.register("platforms", PlatformViewSet, basename="platform")
router.register("entities", EntityViewSet, basename="entity")

# Workspace-scoped resources (workspace_id in path)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/dimensions",
    DimensionViewSet,
    basename="dimension"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/dimension-values",
    DimensionValueViewSet,
    basename="dimensionvalue"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/dimension-constraints",
    DimensionConstraintViewSet,
    basename="dimensionconstraint"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/rules",
    RuleViewSet,
    basename="rule"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/rule-details",
    RuleDetailViewSet,
    basename="ruledetail"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/rule-nested",
    RuleNestedViewSet,
    basename="rule-nested"
)

# Propagation endpoints (workspace-scoped)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/propagation-jobs",
    PropagationJobViewSet,
    basename="propagation-job"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/propagation-errors",
    PropagationErrorViewSet,
    basename="propagation-error"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/enhanced-string-details",
    EnhancedStringDetailViewSet,
    basename="enhanced-stringdetail"
)
router.register(
    r"workspaces/(?P<workspace_id>\d+)/propagation-settings",
    PropagationSettingsViewSet,
    basename="propagation-settings"
)

urlpatterns = [
    path("", include(router.urls)),

    # Main RESTful API endpoints for strings and string details
    path("", include('master_data.urls_main_api')),

    # Project API endpoints (replaces submissions)
    path("", include('master_data.urls_projects')),

    # API version and health endpoints
    path("version/", APIVersionView.as_view(), name="api-version"),
    path("health/", APIHealthView.as_view(), name="api-health"),
    path("demo/", VersionDemoView.as_view(), name="api-version-demo"),

    # Rule configuration endpoints (workspace-scoped)
    path("workspaces/<int:workspace_id>/rules/<int:rule_id>/configuration/",
         RuleConfigurationView.as_view(),
         name="rule-configuration"),

    path("workspaces/<int:workspace_id>/rules/<int:rule_id>/lightweight/",
         LightweightRuleView.as_view(),
         name="rule-lightweight"),

    path("workspaces/<int:workspace_id>/rules/<int:rule_id>/entities/<int:entity_id>/",
         EntitySpecificRuleView.as_view(),
         name="rule-entity-specific"),

    path("workspaces/<int:workspace_id>/rules/<int:rule_id>/validation/",
         RuleValidationView.as_view(),
         name="rule-validation"),

    path("workspaces/<int:workspace_id>/rules/generation-preview/",
         GenerationPreviewView.as_view(),
         name="rule-generation-preview"),

    # Cache management endpoints (workspace-scoped)
    path("workspaces/<int:workspace_id>/rules/cache/invalidate/",
         CacheManagementView.as_view(),
         name="rule-cache-invalidate"),

    path("workspaces/<int:workspace_id>/rules/<int:rule_id>/metrics/",
         CacheManagementView.as_view(),
         name="rule-performance-metrics"),
]
