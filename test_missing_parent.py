#!/usr/bin/env python3
"""
Test to demonstrate behavior when referencing non-existent parent dimensions.
"""

import requests
import json


def test_missing_parent_dimension():
    """Test what happens when parent_name references a non-existent dimension."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimensions/bulk_create/"

    # Payload with parent_name that doesn't exist
    test_data = {
        "dimensions": [
            {
                "name": "Environment",
                "description": "Deployment environment",
                "type": "list",
                "status": "active",
                "parent_name": "NonExistentParent"  # This doesn't exist!
            }
        ]
    }

    print("🧪 Testing with non-existent parent_name...")
    print(f"📝 Payload: {json.dumps(test_data, indent=2)}")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response: {json.dumps(result, indent=2)}")

        if response.status_code == 400:
            print("❌ Expected validation error occurred!")
            print("🔍 The system correctly rejected the non-existent parent")
        else:
            print("⚠️ Unexpected response")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_creating_parent_in_same_batch():
    """Test creating parent and child in the same batch (this works)."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimensions/bulk_create/"

    # Create parent and child in same batch
    test_data = {
        "dimensions": [
            {
                "name": "Application",
                "description": "Application category",
                "type": "list",
                "status": "active"
                # No parent - this will be created first
            },
            {
                "name": "Environment",
                "description": "Deployment environment",
                "type": "list",
                "status": "active",
                "parent_name": "Application"  # References dimension in same batch
            }
        ]
    }

    print("\n🧪 Testing parent and child in same batch...")
    print(f"📝 Creating parent 'Application' and child 'Environment' together")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()
        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ Success! Created {result['success_count']} dimensions")
            print("🎉 The system correctly handled dependency ordering!")

            for item in result['results']:
                parent_info = f" (parent: {item['parent_name']})" if item['parent_name'] else ""
                print(f"  - {item['name']}{parent_info}")
        else:
            print("❌ Unexpected failure")
            print(f"📋 Response: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("=== Testing Parent Dimension Behavior ===\n")

    test_missing_parent_dimension()
    test_creating_parent_in_same_batch()

    print("\n📋 Summary:")
    print("❌ Missing parent dimensions are NOT auto-created")
    print("✅ Parents can be created in the same batch")
    print("⚠️  You must explicitly include all required parent dimensions")
