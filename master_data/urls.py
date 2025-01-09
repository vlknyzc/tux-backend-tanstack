from django.urls import path, include
from rest_framework import routers


from . import api
from . import views


router = routers.DefaultRouter()
router.register("dimensions", api.DimensionViewSet)
router.register("junk-dimension", api.JunkDimensionViewSet)
router.register("workspaces", api.WorkspaceViewSet)
router.register("platforms", api.PlatformViewSet)
router.register("fields", api.FieldViewSet)
router.register("conventions", api.ConventionViewSet)
router.register("convention-platforms", api.ConventionPlatformViewSet)
router.register("structures", api.StructureViewSet)
router.register("strings", api.StringViewSet)
router.register("string-items", api.StringItemViewSet)


urlpatterns = (
    path("api/", include(router.urls)),

)
