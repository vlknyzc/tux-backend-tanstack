from django.views import generic
from django.urls import reverse_lazy
from . import models
from . import forms
from rest_framework import generics
from .serializers import DimensionSerializer
from rest_framework import filters


# class DimensionListView(generic.ListView):
#     model = models.Dimension
#     form_class = forms.DimensionForm

class DimensionListView(generics.ListAPIView):
    queryset = models.Dimension.objects.all()
    serializer_class = DimensionSerializer
    filter_backends = [filters.SearchFilter,
                       filters.OrderingFilter]
    # filterset_fields = ['workspace', 'name']
    search_fields = ['name']


class DimensionCreateView(generic.CreateView):
    model = models.Dimension
    form_class = forms.DimensionForm


class DimensionDetailView(generic.DetailView):
    model = models.Dimension
    form_class = forms.DimensionForm


class DimensionUpdateView(generic.UpdateView):
    model = models.Dimension
    form_class = forms.DimensionForm
    pk_url_kwarg = "pk"


class DimensionDeleteView(generic.DeleteView):
    model = models.Dimension
    success_url = reverse_lazy("master_data_Dimension_list")


class JunkDimensionListView(generic.ListView):
    model = models.JunkDimension
    form_class = forms.JunkDimensionForm


class JunkDimensionCreateView(generic.CreateView):
    model = models.JunkDimension
    form_class = forms.JunkDimensionForm


class JunkDimensionDetailView(generic.DetailView):
    model = models.JunkDimension
    form_class = forms.JunkDimensionForm


class JunkDimensionUpdateView(generic.UpdateView):
    model = models.JunkDimension
    form_class = forms.JunkDimensionForm
    pk_url_kwarg = "pk"


class JunkDimensionDeleteView(generic.DeleteView):
    model = models.JunkDimension
    success_url = reverse_lazy("master_data_JunkDimension_list")


class WorkspaceListView(generic.ListView):
    model = models.Workspace
    form_class = forms.WorkspaceForm


class WorkspaceCreateView(generic.CreateView):
    model = models.Workspace
    form_class = forms.WorkspaceForm


class WorkspaceDetailView(generic.DetailView):
    model = models.Workspace
    form_class = forms.WorkspaceForm


class WorkspaceUpdateView(generic.UpdateView):
    model = models.Workspace
    form_class = forms.WorkspaceForm
    pk_url_kwarg = "pk"


class WorkspaceDeleteView(generic.DeleteView):
    model = models.Workspace
    success_url = reverse_lazy("master_data_Workspace_list")


class PlatformListView(generic.ListView):
    model = models.Platform
    form_class = forms.PlatformForm


class PlatformCreateView(generic.CreateView):
    model = models.Platform
    form_class = forms.PlatformForm


class PlatformDetailView(generic.DetailView):
    model = models.Platform
    form_class = forms.PlatformForm


class PlatformUpdateView(generic.UpdateView):
    model = models.Platform
    form_class = forms.PlatformForm
    pk_url_kwarg = "pk"


class PlatformDeleteView(generic.DeleteView):
    model = models.Platform
    success_url = reverse_lazy("master_data_Platform_list")


class RuleListView(generic.ListView):
    model = models.Rule
    form_class = forms.RuleForm


class RuleCreateView(generic.CreateView):
    model = models.Rule
    form_class = forms.RuleForm


class RuleDetailView(generic.DetailView):
    model = models.Rule
    form_class = forms.RuleForm


class RuleUpdateView(generic.UpdateView):
    model = models.Rule
    form_class = forms.RuleForm
    pk_url_kwarg = "pk"


class RuleDeleteView(generic.DeleteView):
    model = models.Rule
    success_url = reverse_lazy("master_data_Rule_list")


class StructureListView(generic.ListView):
    model = models.Structure
    form_class = forms.StructureForm


class StructureCreateView(generic.CreateView):
    model = models.Structure
    form_class = forms.StructureForm


class StructureDetailView(generic.DetailView):
    model = models.Structure
    form_class = forms.StructureForm


class StructureUpdateView(generic.UpdateView):
    model = models.Structure
    form_class = forms.StructureForm
    pk_url_kwarg = "pk"


class StructureDeleteView(generic.DeleteView):
    model = models.Structure
    success_url = reverse_lazy("master_data_Structure_list")
