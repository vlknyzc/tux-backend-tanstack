from rest_framework import serializers
from .. import models


class SubmissionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Submission
        fields = ['id', 'name', 'slug', 'description', 'status',
                  'rule', 'selected_parent_string', 'starting_field', 'created_by', 'created_by_name', 'created', 'last_updated']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None
