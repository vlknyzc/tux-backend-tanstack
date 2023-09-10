from django import forms
from master_data.models import Dimension
from master_data.models import Dimension
from master_data.models import JunkDimension
# from django.contrib.auth.models import User
from django.conf import settings
from master_data.models import Workspace
from master_data.models import Platform
from master_data.models import Rule
from master_data.models import Dimension
from . import models


# class DimensionForm(forms.ModelForm):
#     class Meta:
#         model = models.Dimension
#         fields = [
#             "definition",
#             "dimension_type",
#             "name",
#             "parent",
#         ]

#     def __init__(self, *args, **kwargs):
#         super(DimensionForm, self).__init__(*args, **kwargs)
#         self.fields["parent"].queryset = Dimension.objects.all()


# class JunkDimensionForm(forms.ModelForm):
#     class Meta:
#         model = models.JunkDimension
#         fields = [
#             "dimension_value_code",
#             "valid_from",
#             "definition",
#             "dimension_value",
#             "valid_until",
#             "dimension_value_label",
#             "dimension_value_utm",
#             "dimension",
#             "parent",
#         ]

#     def __init__(self, *args, **kwargs):
#         super(JunkDimensionForm, self).__init__(*args, **kwargs)
#         self.fields["dimension"].queryset = Dimension.objects.all()
#         self.fields["parent"].queryset = JunkDimension.objects.all()


# class WorkspaceForm(forms.ModelForm):
#     class Meta:
#         model = models.Workspace
#         fields = [
#             "name",
#             "created_by",
#         ]

#     def __init__(self, *args, **kwargs):
#         super(WorkspaceForm, self).__init__(*args, **kwargs)
#         self.fields["created_by"].queryset = settings.AUTH_USER_MODEL.objects.all()


# class PlatformForm(forms.ModelForm):
#     class Meta:
#         model = models.Platform
#         fields = [
#             "platform_type",
#             "name",
#             "platform_field",
#             "workspace",
#         ]

#     def __init__(self, *args, **kwargs):
#         super(PlatformForm, self).__init__(*args, **kwargs)
#         self.fields["workspace"].queryset = Workspace.objects.all()


# class RuleForm(forms.ModelForm):
#     class Meta:
#         model = models.Rule
#         fields = [
#             "valid_from",
#             "valid_until",
#             "workspace",
#             "name",
#         ]

#     def __init__(self, *args, **kwargs):
#         super(RuleForm, self).__init__(*args, **kwargs)
#         # self.fields["platform"].queryset = Platform.objects.all()
#         self.fields["workspace"].queryset = Workspace.objects.all()


# class StructureForm(forms.ModelForm):
#     class Meta:
#         model = models.Structure
#         fields = [
#             "delimeter_after_dimension",
#             "delimeter_before_dimension",
#             "dimension_order",
#             "rule",
#             "dimension",
#         ]

#     def __init__(self, *args, **kwargs):
#         super(StructureForm, self).__init__(*args, **kwargs)
#         self.fields["rule"].queryset = Rule.objects.all()
#         self.fields["dimension"].queryset = Dimension.objects.all()
