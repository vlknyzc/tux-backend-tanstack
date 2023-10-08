from django.views import generic
from django.urls import reverse_lazy
from . import models
# from . import forms
from rest_framework import generics
from .serializers import *
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
# from rest_framework.permissions import IsAuthenticated


# class DimensionListFilter(generics.ListAPIView):
#     queryset = models.Dimension.objects.all()
#     serializer_class = DimensionSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['workspace__id', 'id', 'dimension_type']


# class JunkDimensionListFilter(generics.ListAPIView):
#     queryset = models.JunkDimension.objects.all()
#     serializer_class = JunkDimensionSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['dimension__workspace__id']


class WorkspaceListFilter(generics.ListAPIView):
    queryset = models.Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
