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
    UserViewSet,
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
router.register("users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
