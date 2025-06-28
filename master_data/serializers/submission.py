from rest_framework import serializers
from .. import models
from typing import Optional, Dict, List, Any


class SubmissionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Submission
        fields = ['id', 'name', 'slug', 'description', 'status',
                  'rule', 'selected_parent_string', 'starting_field',
                  'workspace', 'workspace_name', 'created_by', 'created_by_name',
                  'created', 'last_updated']
        read_only_fields = ['workspace_name']

    def get_created_by_name(self, obj) -> Optional[str]:
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_workspace_name(self, obj) -> Optional[str]:
        if obj.workspace:
            return obj.workspace.name
        return None
