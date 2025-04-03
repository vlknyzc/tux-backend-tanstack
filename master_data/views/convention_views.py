# from rest_framework import viewsets, permissions
# from django_filters import rest_framework as filters
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.permissions import IsAuthenticated

# from .. import serializers
# from .. import models


# class ConventionFilter(filters.FilterSet):
#     workspace = filters.NumberFilter(method='filter_workspace_id')

#     class Meta:
#         model = models.Convention
#         fields = ['workspace', 'id']

#     def filter_workspace_id(self, queryset, name, value):
#         return queryset.filter(workspace__id=value)


# class ConventionViewSet(viewsets.ModelViewSet):
#     queryset = models.Convention.objects.all()
#     serializer_class = serializers.ConventionSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = ConventionFilter

#     def get_queryset(self):
#         queryset = models.Convention.objects.all()
#         workspace_id = self.request.query_params.get('workspace_id', None)
#         if workspace_id is not None:
#             queryset = queryset.filter(workspace_id=workspace_id)
#         return queryset


# class ConventionPlatformFilter(filters.FilterSet):
#     workspace = filters.NumberFilter(method='filter_workspace_id')
#     convention = filters.NumberFilter(method='filter_convention_id')

#     class Meta:
#         model = models.ConventionPlatform
#         fields = ['workspace', 'convention']

#     def filter_workspace_id(self, queryset, name, value):
#         return queryset.filter(workspace__id=value)

#     def filter_convention_id(self, queryset, name, value):
#         return queryset.filter(convention__id=value)


# class ConventionPlatformViewSet(viewsets.ModelViewSet):
#     queryset = models.ConventionPlatform.objects.all()
#     serializer_class = serializers.ConventionPlatformSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = ConventionPlatformFilter


# class ConventionPlatformDetailFilter(filters.FilterSet):
#     workspace = filters.NumberFilter(method='filter_workspace_id')

#     class Meta:
#         model = models.ConventionPlatform
#         fields = ['convention', 'platform', 'workspace']

#     def filter_workspace_id(self, queryset, name, value):
#         return queryset.filter(convention__workspace__id=value)


# class ConventionPlatformDetailViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = models.ConventionPlatform.objects.all()
#     serializer_class = serializers.ConventionPlatformDetailSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = ConventionPlatformDetailFilter
