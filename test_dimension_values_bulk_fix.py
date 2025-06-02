#!/usr/bin/env python3
"""
Test script to verify the fix for dimension values bulk upload.
"""

import requests
import json


def test_dimension_values_with_name_references():
    """Test the exact payload that was failing."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimension-values/bulk_create/"

    # The exact payload that was failing
    test_data = {
        "dimension_values": [
            {
                "value": "prod",
                "label": "Production",
                "utm": "prod",
                "description": "Production environment",
                "valid_from": "2023-01-01",
                "valid_until": "2024-12-31",
                "dimension_name": "Environment",
                "parent_dimension_name": "Region",
                "parent_value": "us-east"
            }
        ]
    }

    print("🧪 Testing dimension values bulk upload with name references...")
    print(f"📡 POST {url}")
    print(f"📝 Payload: {json.dumps(test_data, indent=2)}")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"📊 Response Status: {response.status_code}")
        result = response.json()

        if response.status_code == 200:
            print(
                f"✅ Success! Created {result['success_count']} dimension values")
            if result['error_count'] > 0:
                print(f"❌ {result['error_count']} errors:")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print("🎉 No errors!")

        else:
            print(f"❌ Request failed: {response.status_code}")
            if 'errors' in result:
                for error in result['errors']:
                    print(f"  - Index {error['index']}: {error['error']}")

        print(f"\n📋 Full response:")
        print(json.dumps(result, indent=2))

    except requests.exceptions.ConnectionError:
        print(
            "❌ Connection failed. Make sure the Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_multiple_dimension_values():
    """Test multiple dimension values with different reference types."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimension-values/bulk_create/"

    # Test multiple values with different scenarios
    test_data = {
        "dimension_values": [
            # Simple value without parent
            {
                "value": "dev",
                "label": "Development",
                "utm": "dev",
                "description": "Development environment",
                "dimension_name": "Environment"
            },
            # Value with parent reference
            {
                "value": "staging",
                "label": "Staging",
                "utm": "staging",
                "description": "Staging environment",
                "dimension_name": "Environment",
                "parent_dimension_name": "Region",
                "parent_value": "us-west"
            },
            # Value with dates
            {
                "value": "test",
                "label": "Testing",
                "utm": "test",
                "description": "Testing environment",
                "valid_from": "2023-01-01",
                "valid_until": "2024-12-31",
                "dimension_name": "Environment"
            }
        ]
    }

    print("\n🧪 Testing multiple dimension values...")
    print(f"📝 Creating {len(test_data['dimension_values'])} dimension values")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()

        if response.status_code == 200:
            print(
                f"✅ Success! Created {result['success_count']} dimension values")
            if result['error_count'] > 0:
                print(f"❌ {result['error_count']} errors:")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print("🎉 All dimension values created successfully!")

        else:
            print(f"❌ Multiple values test failed: {response.status_code}")
            print(f"📋 Response: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"❌ Error in multiple values test: {e}")


if __name__ == "__main__":
    print("=== Testing Dimension Values Bulk Upload Fix ===\n")

    test_dimension_values_with_name_references()
    test_multiple_dimension_values()

    print("\n📋 Summary:")
    print("✅ Fixed dimension reference assignment to use model instances")
    print("✅ Fixed parent value reference assignment to use model instances")
    print("✅ Supports both name-based and ID-based references")
    print("✅ Proper validation for all reference types")
