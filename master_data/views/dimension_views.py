from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db import transaction

from .. import serializers
from .. import models


class DimensionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Dimension
        fields = ['id', 'workspace', 'type']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(workspace__id=value)


class DimensionViewSet(viewsets.ModelViewSet):
    queryset = models.Dimension.objects.all()
    serializer_class = serializers.DimensionSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new dimension"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    def _create_dimensions_with_dependencies(self, dimensions_data, user):
        """Create dimensions handling parent dependencies within the same batch."""
        results = []
        errors = []
        # name -> dimension instance mapping for batch-created dimensions
        created_dimensions = {}

        # Separate dimensions without dependencies and those with dependencies
        no_deps = [d for d in dimensions_data if '_parent_name' not in d]
        with_deps = [d for d in dimensions_data if '_parent_name' in d]

        # First, create dimensions without dependencies
        for i, dimension_data in enumerate(no_deps):
            try:
                if user.is_authenticated:
                    dimension_data['created_by'] = user

                dimension = models.Dimension.objects.create(**dimension_data)
                created_dimensions[dimension.name] = dimension
                dimension_serializer = self.get_serializer(dimension)
                results.append(dimension_serializer.data)

            except Exception as e:
                errors.append({
                    'index': dimensions_data.index(dimension_data),
                    'dimension_name': dimension_data.get('name', 'Unknown'),
                    'error': str(e)
                })

        # Then create dimensions with dependencies, resolving parent names
        for dimension_data in with_deps:
            try:
                parent_name = dimension_data.pop('_parent_name')

                # Look for parent in created dimensions
                if parent_name in created_dimensions:
                    dimension_data['parent'] = created_dimensions[parent_name]
                else:
                    # This shouldn't happen due to validation, but handle gracefully
                    raise ValueError(
                        f"Parent dimension '{parent_name}' not found in batch")

                if user.is_authenticated:
                    dimension_data['created_by'] = user

                dimension = models.Dimension.objects.create(**dimension_data)
                created_dimensions[dimension.name] = dimension
                dimension_serializer = self.get_serializer(dimension)
                results.append(dimension_serializer.data)

            except Exception as e:
                errors.append({
                    'index': dimensions_data.index(dimension_data),
                    'dimension_name': dimension_data.get('name', 'Unknown'),
                    'error': str(e)
                })

        return results, errors

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple dimensions in a single request."""
        serializer = serializers.DimensionBulkCreateSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    results, errors = self._create_dimensions_with_dependencies(
                        serializer.validated_data['dimensions'],
                        request.user
                    )

                    return Response({
                        'success_count': len(results),
                        'error_count': len(errors),
                        'results': results,
                        'errors': errors
                    })

            except Exception as e:
                return Response(
                    {'error': f'Bulk creation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DimensionValueFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')
    dimension = filters.NumberFilter(method='filter_dimension_id')

    class Meta:
        model = models.DimensionValue
        fields = ['workspace']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(dimension__workspace__id=value)

    def filter_dimension_id(self, queryset, name, value):
        return queryset.filter(dimension__id=value)


class DimensionValueViewSet(viewsets.ModelViewSet):
    queryset = models.DimensionValue.objects.all()
    serializer_class = serializers.DimensionValueSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DimensionValueFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new dimension value"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple dimension values in a single request."""
        serializer = serializers.DimensionValueBulkCreateSerializer(
            data=request.data)

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    results = []
                    errors = []

                    for i, value_data in enumerate(serializer.validated_data['dimension_values']):
                        try:
                            # Set created_by if user is authenticated
                            if request.user.is_authenticated:
                                value_data['created_by'] = request.user

                            dimension_value = models.DimensionValue.objects.create(
                                **value_data)
                            value_serializer = self.get_serializer(
                                dimension_value)
                            results.append(value_serializer.data)

                        except Exception as e:
                            errors.append({
                                'index': i,
                                'dimension_value': value_data.get('value', 'Unknown'),
                                'dimension_id': value_data.get('dimension', 'Unknown'),
                                'error': str(e)
                            })

                    return Response({
                        'success_count': len(results),
                        'error_count': len(errors),
                        'results': results,
                        'errors': errors
                    })

            except Exception as e:
                return Response(
                    {'error': f'Bulk creation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
