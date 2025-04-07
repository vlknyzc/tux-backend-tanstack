from rest_framework import serializers
from .. import models


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Submission
        fields = ['id', 'name', 'description', 'status', 'rule']
