from django.urls import path, include
from rest_framework import routers


from . import api
from . import views


router = routers.DefaultRouter()
router.register("Dimension", api.DimensionViewSet)
router.register("JunkDimension", api.JunkDimensionViewSet)
router.register("Workspace", api.WorkspaceViewSet)
router.register("Platform", api.PlatformViewSet)
router.register("Rule", api.RuleViewSet)
router.register("Structure", api.StructureViewSet)

urlpatterns = (
    path("api/", include(router.urls)),
    path("master_data/Dimension/", views.DimensionListView.as_view(),
         name="master_data_Dimension_list"),
    path("master_data/Dimension/create/", views.DimensionCreateView.as_view(),
         name="master_data_Dimension_create"),
    path("master_data/Dimension/detail/<int:pk>/",
         views.DimensionDetailView.as_view(), name="master_data_Dimension_detail"),
    path("master_data/Dimension/update/<int:pk>/",
         views.DimensionUpdateView.as_view(), name="master_data_Dimension_update"),
    path("master_data/Dimension/delete/<int:pk>/",
         views.DimensionDeleteView.as_view(), name="master_data_Dimension_delete"),
    path("master_data/JunkDimension/", views.JunkDimensionListView.as_view(),
         name="master_data_JunkDimension_list"),
    path("master_data/JunkDimension/create/", views.JunkDimensionCreateView.as_view(),
         name="master_data_JunkDimension_create"),
    path("master_data/JunkDimension/detail/<int:pk>/",
         views.JunkDimensionDetailView.as_view(), name="master_data_JunkDimension_detail"),
    path("master_data/JunkDimension/update/<int:pk>/",
         views.JunkDimensionUpdateView.as_view(), name="master_data_JunkDimension_update"),
    path("master_data/JunkDimension/delete/<int:pk>/",
         views.JunkDimensionDeleteView.as_view(), name="master_data_JunkDimension_delete"),
    path("master_data/Workspace/", views.WorkspaceListView.as_view(),
         name="master_data_Workspace_list"),
    path("master_data/Workspace/create/", views.WorkspaceCreateView.as_view(),
         name="master_data_Workspace_create"),
    path("master_data/Workspace/detail/<int:pk>/",
         views.WorkspaceDetailView.as_view(), name="master_data_Workspace_detail"),
    path("master_data/Workspace/update/<int:pk>/",
         views.WorkspaceUpdateView.as_view(), name="master_data_Workspace_update"),
    path("master_data/Workspace/delete/<int:pk>/",
         views.WorkspaceDeleteView.as_view(), name="master_data_Workspace_delete"),
    path("master_data/Platform/", views.PlatformListView.as_view(),
         name="master_data_Platform_list"),
    path("master_data/Platform/create/", views.PlatformCreateView.as_view(),
         name="master_data_Platform_create"),
    path("master_data/Platform/detail/<int:pk>/",
         views.PlatformDetailView.as_view(), name="master_data_Platform_detail"),
    path("master_data/Platform/update/<int:pk>/",
         views.PlatformUpdateView.as_view(), name="master_data_Platform_update"),
    path("master_data/Platform/delete/<int:pk>/",
         views.PlatformDeleteView.as_view(), name="master_data_Platform_delete"),
    path("master_data/Rule/", views.RuleListView.as_view(),
         name="master_data_Rule_list"),
    path("master_data/Rule/create/", views.RuleCreateView.as_view(),
         name="master_data_Rule_create"),
    path("master_data/Rule/detail/<int:pk>/",
         views.RuleDetailView.as_view(), name="master_data_Rule_detail"),
    path("master_data/Rule/update/<int:pk>/",
         views.RuleUpdateView.as_view(), name="master_data_Rule_update"),
    path("master_data/Rule/delete/<int:pk>/",
         views.RuleDeleteView.as_view(), name="master_data_Rule_delete"),
    path("master_data/Structure/", views.StructureListView.as_view(),
         name="master_data_Structure_list"),
    path("master_data/Structure/create/", views.StructureCreateView.as_view(),
         name="master_data_Structure_create"),
    path("master_data/Structure/detail/<int:pk>/",
         views.StructureDetailView.as_view(), name="master_data_Structure_detail"),
    path("master_data/Structure/update/<int:pk>/",
         views.StructureUpdateView.as_view(), name="master_data_Structure_update"),
    path("master_data/Structure/delete/<int:pk>/",
         views.StructureDeleteView.as_view(), name="master_data_Structure_delete"),




)
