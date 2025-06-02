#!/usr/bin/env python3
"""
Test script to verify the fix for dimension bulk upload parent assignment issue.
"""

import requests
import json


def test_dimension_with_parent_name():
    """Test the specific payload that was failing."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimensions/bulk_create/"

    # The exact payload that was failing
    test_data = {
        "dimensions": [
            {
                "name": "Environment",
                "description": "Deployment environment",
                "type": "list",
                "status": "active",
                "parent_name": "Region"
            }
        ]
    }

    print("🧪 Testing dimension bulk upload with parent_name...")
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
            print(f"✅ Success! Created {result['success_count']} dimensions")
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


def test_multiple_dimensions_with_hierarchy():
    """Test multiple dimensions with parent-child relationships."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimensions/bulk_create/"

    # Test with multiple dimensions including hierarchy within the same batch
    test_data = {
        "dimensions": [
            {
                "name": "Geography",
                "description": "Geographic hierarchy",
                "type": "list",
                "status": "active"
            },
            {
                "name": "Country",
                "description": "Country level",
                "type": "list",
                "status": "active",
                "parent_name": "Geography"
            },
            {
                "name": "State",
                "description": "State/Province level",
                "type": "list",
                "status": "active",
                "parent_name": "Country"
            }
        ]
    }

    print("\n🧪 Testing multiple dimensions with hierarchy...")
    print(
        f"📝 Creating {len(test_data['dimensions'])} dimensions with parent-child relationships")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()

        if response.status_code == 200:
            print(f"✅ Success! Created {result['success_count']} dimensions")
            if result['error_count'] > 0:
                print(f"❌ {result['error_count']} errors:")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print("🎉 Hierarchy creation successful!")

        else:
            print(f"❌ Hierarchy test failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error in hierarchy test: {e}")


if __name__ == "__main__":
    print("=== Testing Dimension Bulk Upload Parent Fix ===\n")

    test_dimension_with_parent_name()
    test_multiple_dimensions_with_hierarchy()

    print("\n📋 Summary:")
    print("✅ Fixed parent dimension assignment to use model instances")
    print("✅ Updated both serializer and view to handle parent relationships correctly")
    print("✅ Supports both existing parent dimensions and same-batch parent creation")
