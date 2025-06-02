#!/usr/bin/env python
"""
Test script to validate new API endpoints and business logic integration.
"""

import django
import os
import sys

# Setup Django BEFORE importing anything Django-related
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

django.setup()


def test_api_endpoints():
    print('=== Testing URL Registration ===')
    try:
        from master_data.urls import router
        print('✓ Master data URLs imported successfully')

        # Count registered endpoints
        url_count = len(router.urls)
        print(f'✓ Found {url_count} registered URL patterns')

    except Exception as e:
        print(f'✗ URL import error: {e}')

    print('\n=== Checking New Custom Actions ===')
    try:
        from master_data.views import StringViewSet, RuleViewSet

        # Check StringViewSet actions
        custom_string_actions = ['generate', 'regenerate',
                                 'check_conflicts', 'bulk_generate', 'hierarchy', 'conflicts']
        for action in custom_string_actions:
            if hasattr(StringViewSet, action):
                print(f'✓ StringViewSet.{action}() - Available')
            else:
                print(f'✗ StringViewSet.{action}() - Missing')

        # Check RuleViewSet actions
        custom_rule_actions = ['preview', 'validate_configuration',
                               'set_default', 'defaults', 'required_dimensions', 'active']
        for action in custom_rule_actions:
            if hasattr(RuleViewSet, action):
                print(f'✓ RuleViewSet.{action}() - Available')
            else:
                print(f'✗ RuleViewSet.{action}() - Missing')

    except Exception as e:
        print(f'✗ ViewSet import error: {e}')


def test_serializers():
    print('\n=== Testing Serializer Imports ===')
    try:
        from master_data.serializers import (
            StringGenerationRequestSerializer,
            StringRegenerationSerializer,
            StringConflictCheckSerializer,
            StringBulkGenerationRequestSerializer,
            RulePreviewRequestSerializer,
            RuleValidationSerializer,
            RuleDetailCreateSerializer,
        )
        print('✓ All new serializers import successfully')
    except ImportError as e:
        print(f'✗ Serializer import error: {e}')


def test_services():
    print('\n=== Testing Service Layer ===')
    try:
        from master_data.services import StringGenerationService, NamingPatternValidator, NamingConventionError
        print('✓ Services import successfully')

        # Test service methods exist
        service_methods = ['generate_string_value', 'validate_dimension_values',
                           'check_naming_conflicts', 'create_string_with_details']
        for method in service_methods:
            if hasattr(StringGenerationService, method):
                print(f'✓ StringGenerationService.{method}() - Available')
            else:
                print(f'✗ StringGenerationService.{method}() - Missing')

    except ImportError as e:
        print(f'✗ Service import error: {e}')


def test_model_enhancements():
    print('\n=== Testing Model Enhancements ===')
    try:
        from master_data.models import String, Rule, RuleDetail

        # Test String model enhancements
        string_methods = ['regenerate_value', 'get_dimension_values',
                          'check_naming_conflicts', 'get_hierarchy_path', 'generate_from_submission']
        for method in string_methods:
            if hasattr(String, method):
                print(f'✓ String.{method}() - Available')
            else:
                print(f'✗ String.{method}() - Missing')

        # Test Rule model enhancements
        rule_methods = ['validate_configuration', 'get_preview',
                        'get_required_dimensions', 'can_generate_for_field', 'get_default_for_platform']
        for method in rule_methods:
            if hasattr(Rule, method):
                print(f'✓ Rule.{method}() - Available')
            else:
                print(f'✗ Rule.{method}() - Missing')

        # Test new fields exist
        string_instance = String()
        new_fields = ['is_auto_generated',
                      'generation_metadata', 'string_uuid']
        for field in new_fields:
            if hasattr(string_instance, field):
                print(f'✓ String.{field} field - Available')
            else:
                print(f'✗ String.{field} field - Missing')

        rule_instance = Rule()
        if hasattr(rule_instance, 'is_default'):
            print(f'✓ Rule.is_default field - Available')
        else:
            print(f'✗ Rule.is_default field - Missing')

    except ImportError as e:
        print(f'✗ Model import error: {e}')


if __name__ == '__main__':
    print('🚀 Testing API Enhancements for String Generation Business Logic\n')
    test_api_endpoints()
    test_serializers()
    test_services()
    test_model_enhancements()
    print('\n✅ Test completed!')
