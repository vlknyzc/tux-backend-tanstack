from django.urls import path, include
from rest_framework import routers


from . import api
from . import views


router = routers.DefaultRouter()
router.register("dimension", api.DimensionViewSet)
router.register("junk-dimension", api.JunkDimensionViewSet)
router.register("workspace", api.WorkspaceViewSet)
router.register("platform", api.PlatformViewSet)
router.register("rule", api.RuleViewSet)
router.register("structure", api.StructureViewSet)


urlpatterns = (
    path("api/", include(router.urls)),

    path("api/filter/dimension/", views.DimensionListFilter.as_view(),
         name="dimension-filter"),

    path("api/filter/junk-dimension/", views.JunkDimensionListFilter.as_view(),
         name="junk-dimension-filter"),

    path("api/filter/workspace/", views.WorkspaceListFilter.as_view(),
         name="workspace-filter"),



    #     path("api/dimension/", views.DimensionListView.as_view(),
    #          name="dimension-list"),
    #     path("api/dimension/create/", views.DimensionCreateView.as_view(),
    #          name="master_data_Dimension_create"),
    #     path("api/dimension/detail/<int:pk>/",
    #          views.DimensionDetailView.as_view(), name="dimension-detail"),
    #     path("master_data/Dimension/update/<int:pk>/",
    #          views.DimensionUpdateView.as_view(), name="master_data_Dimension_update"),
    #     path("api/dimension/delete/<int:pk>/",
    #          views.DimensionDeleteView.as_view(), name="dimension_delete"),
    #     path("master_data/JunkDimension/", views.JunkDimensionListView.as_view(),
    #          name="master_data_JunkDimension_list"),
    #     path("master_data/JunkDimension/create/", views.JunkDimensionCreateView.as_view(),
    #          name="master_data_JunkDimension_create"),
    #     path("master_data/JunkDimension/detail/<int:pk>/",
    #          views.JunkDimensionDetailView.as_view(), name="master_data_JunkDimension_detail"),
    #     path("master_data/JunkDimension/update/<int:pk>/",
    #          views.JunkDimensionUpdateView.as_view(), name="master_data_JunkDimension_update"),
    #     path("master_data/JunkDimension/delete/<int:pk>/",
    #          views.JunkDimensionDeleteView.as_view(), name="master_data_JunkDimension_delete"),
    #     path("master_data/Workspace/", views.WorkspaceListView.as_view(),
    #          name="master_data_Workspace_list"),
    #     path("master_data/Workspace/create/", views.WorkspaceCreateView.as_view(),
    #          name="master_data_Workspace_create"),
    #     path("master_data/Workspace/detail/<int:pk>/",
    #          views.WorkspaceDetailView.as_view(), name="master_data_Workspace_detail"),
    #     path("master_data/Workspace/update/<int:pk>/",
    #          views.WorkspaceUpdateView.as_view(), name="master_data_Workspace_update"),
    #     path("master_data/Workspace/delete/<int:pk>/",
    #          views.WorkspaceDeleteView.as_view(), name="master_data_Workspace_delete"),
    #     path("master_data/Platform/", views.PlatformListView.as_view(),
    #          name="master_data_Platform_list"),
    #     path("master_data/Platform/create/", views.PlatformCreateView.as_view(),
    #          name="master_data_Platform_create"),
    #     path("master_data/Platform/detail/<int:pk>/",
    #          views.PlatformDetailView.as_view(), name="master_data_Platform_detail"),
    #     path("master_data/Platform/update/<int:pk>/",
    #          views.PlatformUpdateView.as_view(), name="master_data_Platform_update"),
    #     path("master_data/Platform/delete/<int:pk>/",
    #          views.PlatformDeleteView.as_view(), name="master_data_Platform_delete"),
    #     path("master_data/Rule/", views.RuleListView.as_view(),
    #          name="master_data_Rule_list"),
    #     path("master_data/Rule/create/", views.RuleCreateView.as_view(),
    #          name="master_data_Rule_create"),
    #     path("master_data/Rule/detail/<int:pk>/",
    #          views.RuleDetailView.as_view(), name="master_data_Rule_detail"),
    #     path("master_data/Rule/update/<int:pk>/",
    #          views.RuleUpdateView.as_view(), name="master_data_Rule_update"),
    #     path("master_data/Rule/delete/<int:pk>/",
    #          views.RuleDeleteView.as_view(), name="master_data_Rule_delete"),
    #     path("master_data/Structure/", views.StructureListView.as_view(),
    #          name="master_data_Structure_list"),
    #     path("master_data/Structure/create/", views.StructureCreateView.as_view(),
    #          name="master_data_Structure_create"),
    #     path("master_data/Structure/detail/<int:pk>/",
    #          views.StructureDetailView.as_view(), name="master_data_Structure_detail"),
    #     path("master_data/Structure/update/<int:pk>/",
    #          views.StructureUpdateView.as_view(), name="master_data_Structure_update"),
    #     path("master_data/Structure/delete/<int:pk>/",
    #          views.StructureDeleteView.as_view(), name="master_data_Structure_delete"),




)
