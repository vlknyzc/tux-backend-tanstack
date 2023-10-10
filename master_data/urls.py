from django.urls import path, include
from rest_framework import routers


from . import api
from . import views

template_router = routers.DefaultRouter()
template_router.register("template-single", api.PlatformTemplateViewSet)
template_router.register("convention-single", api.ConventionSingleViewSet)
template_router.register("field-single", api.FieldSingleViewSet)


router = routers.DefaultRouter()
router.register("dimension", api.DimensionViewSet)
router.register("junk-dimension", api.JunkDimensionViewSet)
router.register("workspace", api.WorkspaceViewSet)
router.register("platform", api.PlatformViewSet)
router.register("field", api.FieldViewSet)
router.register("convention", api.ConventionViewSet)
router.register("structure", api.StructureViewSet)


urlpatterns = (
    path("api/", include(router.urls)),
    path("api/", include(template_router.urls)),
)
