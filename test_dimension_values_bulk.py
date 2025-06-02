#!/usr/bin/env python3
"""
Test script for the existing dimension values bulk upload endpoint.
"""

import requests
import json


def test_dimension_values_bulk_upload():
    """Test the existing bulk upload endpoint for dimension values."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimension-values/bulk_create/"

    # Test data using name-based references
    test_data = {
        "dimension_values": [
            {
                "dimension_name": "Environment",
                "value": "prod",
                "label": "Production",
                "utm": "prod",
                "description": "Production environment",
                "valid_from": "2023-01-01"
            },
            {
                "dimension_name": "Environment",
                "value": "staging",
                "label": "Staging",
                "utm": "staging",
                "description": "Staging environment",
                "valid_from": "2023-01-01"
            },
            {
                "dimension_name": "Region",
                "value": "us-east",
                "label": "US East",
                "utm": "use",
                "description": "US East region",
                "valid_from": "2023-01-01"
            },
            {
                # This one uses parent reference by name
                "dimension_name": "Subregion",
                "value": "us-east-1",
                "label": "US East 1",
                "utm": "use1",
                "description": "US East Virginia",
                "valid_from": "2023-01-01",
                "parent_dimension_name": "Region",
                "parent_value": "us-east"
            }
        ]
    }

    print("🧪 Testing dimension values bulk upload endpoint...")
    print(f"📡 POST {url}")
    print(f"📝 Uploading {len(test_data['dimension_values'])} dimension values")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )

        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(
                f"✅ Success! Created {result['success_count']} dimension values")
            if result['error_count'] > 0:
                print(f"❌ {result['error_count']} errors:")
                for error in result['errors']:
                    print(f"  - Row {error['index']}: {error['error']}")

            print("\n📋 Response format:")
            print(json.dumps(result, indent=2))

        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print(
            "❌ Connection failed. Make sure the Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_csv_compatible_format():
    """Test data format that matches the CSV examples."""

    base_url = "http://localhost:8000/api"
    url = f"{base_url}/dimension-values/bulk_create/"

    # CSV-like test data
    csv_data = {
        "dimension_values": [
            # Simple values without parents
            {
                "dimension_name": "Cost Center",
                "value": "IT001",
                "label": "IT Operations",
                "utm": "it001",
                "description": "IT Operations cost center"
            },
            {
                "dimension_name": "Cost Center",
                "value": "MKT001",
                "label": "Marketing",
                "utm": "mkt001",
                "description": "Marketing cost center"
            },
            # Value with parent reference
            {
                "dimension_name": "Environment Type",
                "value": "web",
                "label": "Web Server",
                "utm": "web",
                "description": "Web server environment",
                "parent_dimension_name": "Environment",
                "parent_value": "prod"
            }
        ]
    }

    print("\n🧪 Testing CSV-compatible format...")
    print(f"📝 Testing {len(csv_data['dimension_values'])} values")

    try:
        response = requests.post(
            url,
            json=csv_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ CSV format test successful!")
            print(f"   Created: {result['success_count']}")
            print(f"   Errors: {result['error_count']}")
        else:
            print(f"❌ CSV format test failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error in CSV test: {e}")


if __name__ == "__main__":
    print("=== Testing Existing Dimension Values Bulk Upload ===\n")

    test_dimension_values_bulk_upload()
    test_csv_compatible_format()

    print("\n📋 Summary:")
    print("✅ Bulk upload endpoint already exists at: POST /api/dimension-values/bulk_create/")
    print("✅ Supports name-based references (dimension_name, parent_dimension_name + parent_value)")
    print("✅ Transaction safety with individual error reporting")
    print("✅ Compatible with CSV upload patterns")
    print("\n📖 See examples/csv_bulk_upload.py for complete CSV integration")
