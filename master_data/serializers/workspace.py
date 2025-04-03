from rest_framework import serializers
from .. import models


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Workspace
        fields = [
            "id",
            "name",
            "logo",
            "created_by",
            "created",
            "last_updated",
        ]
        read_only_fields = ["created", "last_updated"]
