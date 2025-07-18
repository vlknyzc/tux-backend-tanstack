#!/usr/bin/env python3
"""
Test script to verify the get_rule_configuration_data method returns correct structure.
This can be run locally without authentication.
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()


def test_rule_configuration_method():
    """Test the get_rule_configuration_data method"""

    # Import after Django is set up
    from master_data.services.rule_service import RuleService
    from master_data.models import Rule

    service = RuleService()

    # Get the first available rule
    try:
        rule = Rule.objects.first()
        if not rule:
            print("No rules found in database")
            return

        print(f"Testing with rule: {rule.id} - {rule.name}")

        # Get configuration data
        config_data = service.get_rule_configuration_data(rule.id)

        # Check expected structure
        expected_keys = ['id', 'name', 'slug', 'platform', 'workspace', 'fields',
                         'dimensions', 'dimension_values', 'generated_at', 'created_by']

        print("\n=== Response Structure Check ===")
        for key in expected_keys:
            if key in config_data:
                print(f"✓ {key}: {type(config_data[key])}")
            else:
                print(f"✗ Missing: {key}")

        # Check for unexpected keys
        unexpected_keys = ['rule', 'rule_name', 'rule_slug',
                           'field_templates', 'dimension_catalog', 'metadata']
        print("\n=== Checking for Wrong Response Type ===")
        for key in unexpected_keys:
            if key in config_data:
                print(
                    f"⚠ Found unexpected key: {key} - This suggests wrong response type!")
            else:
                print(f"✓ No unexpected key: {key}")

        # Check nested structure
        print("\n=== Nested Structure Check ===")

        # Check platform structure
        if 'platform' in config_data:
            platform = config_data['platform']
            if isinstance(platform, dict) and 'id' in platform and 'name' in platform and 'slug' in platform:
                print("✓ Platform structure is correct")
            else:
                print("✗ Platform structure is incorrect")

        # Check workspace structure
        if 'workspace' in config_data:
            workspace = config_data['workspace']
            if isinstance(workspace, dict) and 'id' in workspace and 'name' in workspace:
                print("✓ Workspace structure is correct")
            else:
                print("✗ Workspace structure is incorrect")

        # Check fields structure
        if 'fields' in config_data:
            fields = config_data['fields']
            if isinstance(fields, list):
                print(f"✓ Fields is a list with {len(fields)} items")
                if fields:
                    first_field = fields[0]
                    if 'id' in first_field and 'name' in first_field and 'field_items' in first_field:
                        print("✓ First field structure is correct")
                    else:
                        print("✗ First field structure is incorrect")
            else:
                print("✗ Fields is not a list")

        # Check dimensions structure
        if 'dimensions' in config_data:
            dimensions = config_data['dimensions']
            if isinstance(dimensions, dict):
                print(f"✓ Dimensions is a dict with {len(dimensions)} items")
            else:
                print("✗ Dimensions is not a dict")

        # Check dimension_values structure
        if 'dimension_values' in config_data:
            dimension_values = config_data['dimension_values']
            if isinstance(dimension_values, dict):
                print(
                    f"✓ Dimension values is a dict with {len(dimension_values)} items")
            else:
                print("✗ Dimension values is not a dict")

        print(f"\n=== Sample Response ===")
        print(json.dumps(config_data, indent=2, default=str)[:1000] + "..." if len(json.dumps(
            config_data, default=str)) > 1000 else json.dumps(config_data, indent=2, default=str))

    except Exception as e:
        print(f"Error testing method: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_rule_configuration_method()
