#!/usr/bin/env python3
"""
Test script to verify rule configuration endpoint returns correct structure.
This script can be used to test the endpoint and clear cache if needed.
"""

import requests
import json
import sys


def test_rule_configuration(rule_id, base_url="https://tux-prod.up.railway.app"):
    """Test the rule configuration endpoint"""

    url = f"{base_url}/api/v1/rules/{rule_id}/configuration/"

    print(f"Testing rule configuration endpoint: {url}")

    try:
        response = requests.get(url)

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()

            # Check if response has the expected structure
            expected_keys = ['id', 'name', 'slug', 'platform', 'workspace', 'fields',
                             'dimensions', 'dimension_values', 'generated_at', 'created_by']

            print("\n=== Response Structure Check ===")
            for key in expected_keys:
                if key in data:
                    print(f"✓ {key}: {type(data[key])}")
                else:
                    print(f"✗ Missing: {key}")

            # Check for unexpected keys that might indicate wrong response type
            unexpected_keys = ['rule', 'rule_name', 'rule_slug',
                               'field_templates', 'dimension_catalog', 'metadata']
            print("\n=== Checking for Wrong Response Type ===")
            for key in unexpected_keys:
                if key in data:
                    print(
                        f"⚠ Found unexpected key: {key} - This suggests wrong response type!")
                else:
                    print(f"✓ No unexpected key: {key}")

            print(f"\n=== Sample Response ===")
            print(json.dumps(data, indent=2)[
                  :1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))

        else:
            print(f"Error Response: {response.text}")

    except Exception as e:
        print(f"Error testing endpoint: {str(e)}")


def clear_cache(rule_id, base_url="https://tux-prod.up.railway.app"):
    """Clear cache for the rule"""

    url = f"{base_url}/api/v1/rules/cache/invalidate/"
    payload = {"rule_ids": [rule_id]}

    print(f"Clearing cache for rule {rule_id}")

    try:
        response = requests.post(url, json=payload)
        print(f"Cache clear status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error clearing cache: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python test_rule_configuration.py <rule_id> [clear_cache]")
        sys.exit(1)

    rule_id = int(sys.argv[1])
    clear_cache_flag = len(sys.argv) > 2 and sys.argv[2] == "clear_cache"

    if clear_cache_flag:
        clear_cache(rule_id)
        print("\n" + "="*50 + "\n")

    test_rule_configuration(rule_id)
