from rest_framework import viewsets, permissions, filters
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .. import models
from ..serializers.submission import SubmissionSerializer


class SubmissionFilter(filters.FilterSet):
    workspace = filters.NumberFilter(method='filter_workspace_id')

    class Meta:
        model = models.Submission
        fields = ['id']

    def filter_workspace_id(self, queryset, name, value):
        return queryset.filter(workspace__id=value)


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = models.Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.AllowAny] if settings.DEBUG else [
        permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubmissionFilter

    def perform_create(self, serializer):
        """Set created_by to the current user when creating a new submission"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
