"""
Response serializers for API response data formatting.

This module contains serializers responsible for formatting
API responses related to rules, health checks, and system info.
"""

from rest_framework import serializers


class APIVersionResponseSerializer(serializers.Serializer):
    """Serializer for API version responses"""
    version = serializers.CharField()
    message = serializers.CharField()
    features = serializers.ListField(child=serializers.CharField())
    deprecated_features = serializers.ListField(
        child=serializers.CharField(), required=False)
    breaking_changes = serializers.ListField(
        child=serializers.CharField(), required=False)
    debug_info = serializers.DictField(required=False)


class APIHealthResponseSerializer(serializers.Serializer):
    """Serializer for API health check responses"""
    status = serializers.CharField()
    version = serializers.CharField()
    timestamp = serializers.CharField()
    database = serializers.CharField()
    cache = serializers.CharField()
    workspace_detection = serializers.CharField()
    debug_info = serializers.DictField()


class VersionDemoResponseSerializer(serializers.Serializer):
    """Serializer for version demo responses"""
    message = serializers.CharField()
    timestamp = serializers.CharField()
    version = serializers.CharField()
    data = serializers.DictField()
    debug_info = serializers.DictField()
    links = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)
    performance_metrics = serializers.DictField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses"""
    error = serializers.CharField()
    supported_versions = serializers.ListField(
        child=serializers.CharField(), required=False)
    debug_info = serializers.DictField(required=False)


class CacheInvalidationResponseSerializer(serializers.Serializer):
    """Serializer for cache invalidation responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    rule_ids = serializers.ListField(child=serializers.IntegerField())
    workspace = serializers.IntegerField()
    timestamp = serializers.CharField()


class GenerationPreviewResponseSerializer(serializers.Serializer):
    """Serializer for generation preview responses"""
    preview = serializers.CharField()
    rule_id = serializers.IntegerField()
    field_id = serializers.IntegerField(required=False)
    sample_values = serializers.DictField()
    generation_time_ms = serializers.FloatField()
    workspace = serializers.IntegerField()
