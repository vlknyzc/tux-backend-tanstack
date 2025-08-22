"""
Examples for the multi-operations validate endpoint.
Demonstrates how to validate operations before executing them.
"""

import requests
import json
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
WORKSPACE_ID = 1
AUTH_TOKEN = "your_auth_token_here"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def validate_operations(operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate operations without executing them.
    
    Args:
        operations: List of operation dictionaries
        
    Returns:
        Validation response data
    """
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/multi-operations/validate/"
    
    payload = {"operations": operations}
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Validation Response Status: {response.status_code}")
    result = response.json()
    
    if result.get('status') == 'valid':
        print("✅ Validation PASSED")
        print(f"   Status: {result['status']}")
        print(f"   Total operations: {result['total_operations']}")
        print(f"   Message: {result['message']}")
    else:
        print("❌ Validation FAILED")
        print(f"   Status: {result['status']}")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Total operations: {result.get('total_operations', 0)}")
    
    return result

# =============================================================================
# EXAMPLE 1: Valid Operations
# =============================================================================

def example_1_valid_operations():
    """Example: Validate operations that should pass."""
    print("\n=== Example 1: Valid Operations ===")
    
    operations = [
        {
            "type": "update_string_detail",
            "data": [
                {"id": 154, "dimension_value": 3},
                {"id": 157, "dimension_value_freetext": "updated_value"}
            ]
        },
        {
            "type": "update_string_parent",
            "data": {"string_id": 88, "parent_id": 45}
        },
        {
            "type": "create_string_detail",
            "data": {
                "string": 85,
                "dimension": 10,
                "dimension_value": 20
            }
        }
    ]
    
    return validate_operations(operations)

# =============================================================================
# EXAMPLE 2: Invalid Operation Type
# =============================================================================

def example_2_invalid_operation_type():
    """Example: Validate operations with invalid operation type."""
    print("\n=== Example 2: Invalid Operation Type ===")
    
    operations = [
        {
            "type": "invalid_operation_type",  # This will fail
            "data": {"id": 154, "dimension_value": 3}
        }
    ]
    
    return validate_operations(operations)

# =============================================================================
# EXAMPLE 3: Missing Required Fields
# =============================================================================

def example_3_missing_fields():
    """Example: Validate operations with missing required fields."""
    print("\n=== Example 3: Missing Required Fields ===")
    
    operations = [
        {
            # Missing 'type' field
            "data": {"id": 154, "dimension_value": 3}
        },
        {
            "type": "update_string_detail"
            # Missing 'data' field
        }
    ]
    
    return validate_operations(operations)

# =============================================================================
# EXAMPLE 4: Invalid Data Format
# =============================================================================

def example_4_invalid_data_format():
    """Example: Validate operations with invalid data format."""
    print("\n=== Example 4: Invalid Data Format ===")
    
    operations = [
        {
            "type": "update_string_detail",
            "data": "invalid_data_type"  # Should be object or array
        },
        {
            "type": "create_string_detail",
            "data": []  # Empty array not allowed
        },
        {
            "type": "delete_string",
            "data": [
                {"id": 88},
                "invalid_item_type"  # Array items must be objects
            ]
        }
    ]
    
    return validate_operations(operations)

# =============================================================================
# EXAMPLE 5: Empty Operations List
# =============================================================================

def example_5_empty_operations():
    """Example: Validate empty operations list."""
    print("\n=== Example 5: Empty Operations List ===")
    
    operations = []  # Empty list not allowed
    
    return validate_operations(operations)

# =============================================================================
# EXAMPLE 6: Complex Valid Operations with Arrays
# =============================================================================

def example_6_complex_valid_operations():
    """Example: Complex valid operations using array format."""
    print("\n=== Example 6: Complex Valid Operations with Arrays ===")
    
    operations = [
        # Bulk create string details
        {
            "type": "create_string_detail",
            "data": [
                {
                    "string": 85,
                    "dimension": 10,
                    "dimension_value": 20
                },
                {
                    "string": 86,
                    "dimension": 11,
                    "dimension_value_freetext": "bulk_value_1"
                },
                {
                    "string": 87,
                    "dimension": 12,
                    "dimension_value": 25
                }
            ]
        },
        # Bulk update string details
        {
            "type": "update_string_detail",
            "data": [
                {"id": 150, "dimension_value_freetext": "updated_1"},
                {"id": 151, "dimension_value": 30},
                {"id": 152, "dimension_value_freetext": "updated_2"}
            ]
        },
        # Single string creation
        {
            "type": "create_string",
            "data": {
                "field": 42,
                "submission": 123,
                "details": [
                    {"dimension": 8, "dimension_value": 25},
                    {"dimension": 12, "dimension_value_freetext": "custom"}
                ]
            }
        },
        # Bulk delete operations
        {
            "type": "delete_string_detail",
            "data": [
                {"id": 140},
                {"id": 141},
                {"id": 142}
            ]
        }
    ]
    
    return validate_operations(operations)

# =============================================================================
# EXAMPLE 7: Mixed Valid and Invalid Scenarios
# =============================================================================

def example_7_validation_workflow():
    """Example: Demonstrate validation workflow for different scenarios."""
    print("\n=== Example 7: Validation Workflow ===")
    
    # Test different scenarios
    scenarios = [
        {
            "name": "Valid grouped operations",
            "operations": [
                {
                    "type": "update_string_detail",
                    "data": [
                        {"id": 154, "dimension_value": 3},
                        {"id": 157, "dimension_value_freetext": "2"}
                    ]
                }
            ]
        },
        {
            "name": "Invalid operation type",
            "operations": [
                {
                    "type": "nonexistent_operation",
                    "data": {"id": 154}
                }
            ]
        },
        {
            "name": "Valid mixed operations",
            "operations": [
                {
                    "type": "create_submission",
                    "data": {
                        "name": "Test Submission",
                        "rule": 15,
                        "status": "draft"
                    }
                },
                {
                    "type": "update_string_parent",
                    "data": {"string_id": 88, "parent_id": 45}
                }
            ]
        }
    ]
    
    results = []
    for scenario in scenarios:
        print(f"\n--- Testing: {scenario['name']} ---")
        result = validate_operations(scenario['operations'])
        results.append({
            'scenario': scenario['name'],
            'result': result
        })
    
    return results

# =============================================================================
# SAMPLE RESPONSES DOCUMENTATION
# =============================================================================

def show_sample_responses():
    """Display sample responses for documentation."""
    print("\n=== SAMPLE RESPONSES ===")
    
    print("\n1. VALID OPERATIONS RESPONSE:")
    print("Status Code: 200 OK")
    print(json.dumps({
        "status": "valid",
        "total_operations": 3,
        "message": "All operations are valid and ready for execution"
    }, indent=2))
    
    print("\n2. INVALID OPERATIONS RESPONSE:")
    print("Status Code: 200 OK")  # Note: Still 200, not 400
    print(json.dumps({
        "status": "invalid",
        "error": "Unknown operation type: invalid_operation_type",
        "total_operations": 0
    }, indent=2))
    
    print("\n3. MISSING FIELDS RESPONSE:")
    print("Status Code: 200 OK")
    print(json.dumps({
        "status": "invalid",
        "error": "Operation 0 missing 'type' field",
        "total_operations": 0
    }, indent=2))
    
    print("\n4. EMPTY OPERATIONS RESPONSE:")
    print("Status Code: 200 OK")
    print(json.dumps({
        "status": "invalid",
        "error": "At least one operation must be provided",
        "total_operations": 0
    }, indent=2))
    
    print("\n5. INVALID DATA FORMAT RESPONSE:")
    print("Status Code: 200 OK")
    print(json.dumps({
        "status": "invalid",
        "error": "Operation 0 'data' must be an object or array",
        "total_operations": 0
    }, indent=2))

# =============================================================================
# VALIDATION CHECKLIST
# =============================================================================

def show_validation_checklist():
    """Display what the validate endpoint checks."""
    print("\n=== VALIDATION CHECKLIST ===")
    
    checks = [
        "✅ Operations list is not empty",
        "✅ Each operation has 'type' field",
        "✅ Each operation has 'data' field", 
        "✅ Operation type is supported",
        "✅ Data is object or array (not string/number)",
        "✅ If data is array, it's not empty",
        "✅ If data is array, all items are objects",
        "✅ JSON structure is valid",
        "✅ Request format matches schema"
    ]
    
    print("\nThe validate endpoint performs these checks:")
    for check in checks:
        print(f"  {check}")
    
    print(f"\nSupported operation types:")
    operation_types = [
        "create_string", "update_string", "delete_string",
        "create_string_detail", "update_string_detail", "delete_string_detail", 
        "create_submission", "update_submission", "delete_submission",
        "update_string_parent"
    ]
    
    for op_type in operation_types:
        print(f"  • {op_type}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🔍 Multi-Operations Validate Endpoint Examples")
    print("==============================================")
    
    # Show what validation checks
    show_validation_checklist()
    
    # Show sample responses
    show_sample_responses()
    
    # Run validation examples
    try:
        example_1_valid_operations()
        example_2_invalid_operation_type()
        example_3_missing_fields()
        example_4_invalid_data_format()
        example_5_empty_operations()
        example_6_complex_valid_operations()
        example_7_validation_workflow()
        
    except Exception as e:
        print(f"❌ Example execution failed: {str(e)}")
    
    print("\n✨ Validation examples completed!")
    print("\nKey Points:")
    print("• Validation endpoint always returns 200 OK")
    print("• Check 'status' field: 'valid' or 'invalid'")
    print("• Use validation before execute for safety")
    print("• Validation is fast - no database operations")
    print("• Catches structure/format errors early")

