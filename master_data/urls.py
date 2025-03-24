from django.urls import path, include
from rest_framework import routers


from . import api
from . import views


router = routers.DefaultRouter()
router.register("dimensions", api.DimensionViewSet)
router.register("dimension-values", api.DimensionValueViewSet)
router.register("workspaces", api.WorkspaceViewSet)
router.register("platforms", api.PlatformViewSet)
router.register("fields", api.FieldViewSet)
router.register("conventions", api.ConventionViewSet)
router.register("convention-platforms",
                api.ConventionPlatformViewSet, basename="convention-platforms")
router.register("convention-platforms-detail",
                api.ConventionPlatformDetailViewSet, basename="convention-platforms-detail")
router.register("rules", api.RuleViewSet)
router.register("rule-details", api.RuleDetailViewSet)
router.register("submissions", api.SubmissionViewSet)
router.register("strings", api.StringViewSet)
router.register("string-details", api.StringDetailViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
