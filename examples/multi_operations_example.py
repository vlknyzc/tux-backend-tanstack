"""
Example usage of the multi-operations endpoint.
Demonstrates atomic create, update, and delete operations across different models.

The multi-operations endpoint provides "all or nothing" transaction guarantees:
- All operations succeed together, or all fail together
- No partial updates if any operation fails
- Single API call for complex multi-step operations
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


def execute_multi_operations(operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Execute multiple operations atomically.
    
    Args:
        operations: List of operation dictionaries
        
    Returns:
        API response data
    """
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/multi-operations/execute/"
    
    payload = {"operations": operations}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Multi-operation transaction completed successfully!")
        print(f"   Transaction ID: {result['transaction_id']}")
        print(f"   Total operations: {result['total_operations']}")
        print(f"   Successful operations: {result['successful_operations']}")
        
        for op_result in result['results']:
            print(f"   Operation {op_result['operation_index']}: {op_result['type']} - {op_result['status']}")
        
        return result
    else:
        print(f"❌ Multi-operation transaction failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return response.json() if response.content else {}


def validate_operations(operations: List[Dict[str, Any]]) -> bool:
    """
    Validate operations without executing them.
    
    Args:
        operations: List of operation dictionaries
        
    Returns:
        True if valid, False otherwise
    """
    url = f"{BASE_URL}/workspaces/{WORKSPACE_ID}/multi-operations/validate/"
    
    payload = {"operations": operations}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'valid':
            print("✅ Operations validation passed!")
            print(f"   Total operations: {result['total_operations']}")
            return True
        else:
            print("❌ Operations validation failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
    else:
        print(f"❌ Validation request failed: {response.status_code}")
        return False


# =============================================================================
# EXAMPLE 1: Update String Details and Change Parent
# =============================================================================

def example_1_update_details_and_parent():
    """
    Example: Update string details and change string parent in one transaction.
    
    This solves the original problem where you need to update string detail
    values AND change the string parent relationship atomically.
    
    NEW: Uses grouped array format for multiple string detail updates!
    """
    print("\n=== Example 1: Update String Details and Change Parent (Grouped) ===")
    
    operations = [
        {
            "type": "update_string_detail",
            "data": [
                {
                    "id": 154,
                    "dimension_value": 3  # Change dimension value
                },
                {
                    "id": 157,
                    "dimension_value_freetext": "2"  # Change freetext value
                }
            ]
        },
        {
            "type": "update_string_parent",
            "data": {
                "string_id": 88,
                "parent_id": 45  # Change parent relationship
            }
        }
    ]
    
    # Validate first
    if validate_operations(operations):
        # Execute if validation passes
        result = execute_multi_operations(operations)
        if result and 'results' in result:
            print(f"   Total operation groups: {result['total_operations']}")
            print(f"   Total individual operations: {result['total_individual_operations']}")
            for op_result in result['results']:
                print(f"   Operation {op_result['operation_index']}: {op_result['type']} - {op_result['count']} items")
        return result
    else:
        print("Skipping execution due to validation errors")
        return None


def example_1b_update_details_and_parent_individual():
    """
    Example: Same as example 1 but using individual operations format.
    
    This demonstrates the old way vs the new grouped way.
    """
    print("\n=== Example 1b: Update String Details and Change Parent (Individual) ===")
    
    operations = [
        {
            "type": "update_string_detail",
            "data": {
                "id": 154,
                "dimension_value": 3  # Change dimension value
            }
        },
        {
            "type": "update_string_detail", 
            "data": {
                "id": 157,
                "dimension_value_freetext": "2"  # Change freetext value
            }
        },
        {
            "type": "update_string_parent",
            "data": {
                "string_id": 88,
                "parent_id": 45  # Change parent relationship
            }
        }
    ]
    
    # Validate first
    if validate_operations(operations):
        # Execute if validation passes
        result = execute_multi_operations(operations)
        if result and 'results' in result:
            print(f"   Total operation groups: {result['total_operations']}")
            print(f"   Total individual operations: {result['total_individual_operations']}")
        return result
    else:
        print("Skipping execution due to validation errors")
        return None


# =============================================================================
# EXAMPLE 2: Create Complex String with Details
# =============================================================================

def example_2_create_complex_string():
    """
    Example: Create a string with multiple details in one transaction.
    """
    print("\n=== Example 2: Create Complex String with Details ===")
    
    operations = [
        {
            "type": "create_string",
            "data": {
                "field": 42,
                "submission": 123,
                "details": [
                    {
                        "dimension": 8,
                        "dimension_value": 25
                    },
                    {
                        "dimension": 12,
                        "dimension_value": 50
                    },
                    {
                        "dimension": 15,
                        "dimension_value_freetext": "custom_value"
                    }
                ]
            }
        }
    ]
    
    if validate_operations(operations):
        result = execute_multi_operations(operations)
        if result and 'results' in result:
            string_result = result['results'][0]['result']
            print(f"   Created string: ID={string_result['id']}, Value='{string_result['value']}'")
        return result
    else:
        print("Skipping execution due to validation errors")
        return None


# =============================================================================
# EXAMPLE 3: Complex Workflow - Create, Update, and Link
# =============================================================================

def example_3_complex_workflow():
    """
    Example: Complex workflow involving creation, updates, and linking.
    """
    print("\n=== Example 3: Complex Workflow - Create, Update, and Link ===")
    
    operations = [
        # Step 1: Create a new submission
        {
            "type": "create_submission",
            "data": {
                "name": "Multi-Op Test Submission",
                "rule": 15,
                "status": "draft"
            }
        },
        # Step 2: Create a parent string
        {
            "type": "create_string",
            "data": {
                "field": 40,
                "submission": 123,  # Will be updated with new submission ID
                "details": [
                    {
                        "dimension": 8,
                        "dimension_value": 30
                    }
                ]
            }
        },
        # Step 3: Create a child string
        {
            "type": "create_string", 
            "data": {
                "field": 41,
                "submission": 123,  # Will be updated with new submission ID
                "details": [
                    {
                        "dimension": 8,
                        "dimension_value": 30
                    },
                    {
                        "dimension": 12,
                        "dimension_value": 55
                    }
                ]
            }
        }
        # Note: In a real scenario, you'd need to handle the dynamic IDs
        # from created objects in subsequent operations
    ]
    
    if validate_operations(operations):
        result = execute_multi_operations(operations)
        return result
    else:
        print("Skipping execution due to validation errors")
        return None


# =============================================================================
# EXAMPLE 4: Bulk Delete Operations
# =============================================================================

def example_4_bulk_delete():
    """
    Example: Delete multiple entities in one transaction.
    """
    print("\n=== Example 4: Bulk Delete Operations ===")
    
    operations = [
        {
            "type": "delete_string_detail",
            "data": {
                "id": 154
            }
        },
        {
            "type": "delete_string_detail",
            "data": {
                "id": 157
            }
        },
        {
            "type": "delete_string",
            "data": {
                "id": 88
            }
        }
    ]
    
    if validate_operations(operations):
        result = execute_multi_operations(operations)
        return result
    else:
        print("Skipping execution due to validation errors")
        return None


# =============================================================================
# EXAMPLE 5: Bulk Operations with Arrays
# =============================================================================

def example_5_bulk_operations_with_arrays():
    """
    Example: Demonstrate bulk operations using array format for efficiency.
    """
    print("\n=== Example 5: Bulk Operations with Arrays ===")
    
    operations = [
        # Bulk create multiple string details
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
        # Bulk update multiple string details
        {
            "type": "update_string_detail",
            "data": [
                {
                    "id": 150,
                    "dimension_value_freetext": "updated_value_1"
                },
                {
                    "id": 151,
                    "dimension_value": 30
                },
                {
                    "id": 152,
                    "dimension_value_freetext": "updated_value_2"
                }
            ]
        },
        # Bulk delete multiple string details
        {
            "type": "delete_string_detail",
            "data": [
                {"id": 140},
                {"id": 141},
                {"id": 142}
            ]
        }
    ]
    
    if validate_operations(operations):
        result = execute_multi_operations(operations)
        if result and 'results' in result:
            print(f"   Processed {result['total_individual_operations']} individual operations in {result['total_operations']} groups")
            for op_result in result['results']:
                print(f"   {op_result['type']}: {op_result['count']} items processed")
        return result
    else:
        print("Skipping execution due to validation errors")
        return None


# =============================================================================
# EXAMPLE 6: Mixed Operations Workflow
# =============================================================================

def example_5_mixed_operations():
    """
    Example: Mixed create, update, and delete operations.
    """
    print("\n=== Example 5: Mixed Operations Workflow ===")
    
    operations = [
        # Create a new string detail
        {
            "type": "create_string_detail",
            "data": {
                "string": 85,
                "dimension": 10,
                "dimension_value": 20
            }
        },
        # Update an existing string detail
        {
            "type": "update_string_detail",
            "data": {
                "id": 150,
                "dimension_value_freetext": "updated_value"
            }
        },
        # Update a submission
        {
            "type": "update_submission",
            "data": {
                "id": 120,
                "status": "active",
                "name": "Updated Submission Name"
            }
        },
        # Delete an old string detail
        {
            "type": "delete_string_detail",
            "data": {
                "id": 140
            }
        }
    ]
    
    if validate_operations(operations):
        result = execute_multi_operations(operations)
        return result
    else:
        print("Skipping execution due to validation errors")
        return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def demonstrate_rollback_behavior():
    """
    Demonstrate that operations are rolled back when one fails.
    """
    print("\n=== Rollback Behavior Demonstration ===")
    
    operations = [
        # Valid operation
        {
            "type": "update_string_detail",
            "data": {
                "id": 154,
                "dimension_value": 3
            }
        },
        # Invalid operation (non-existent ID)
        {
            "type": "update_string_detail",
            "data": {
                "id": 99999,  # This ID doesn't exist
                "dimension_value": 5
            }
        }
    ]
    
    print("Attempting operations where one will fail...")
    result = execute_multi_operations(operations)
    
    if not result or result.get('status') == 'failed':
        print("✅ Rollback behavior confirmed: All operations were rolled back")
    else:
        print("❌ Unexpected: Transaction should have failed")


def get_operation_types_help():
    """
    Display help information about supported operation types.
    """
    print("\n=== Supported Operation Types ===")
    
    operation_types = {
        "String Operations": [
            "create_string - Create new string with details",
            "update_string - Update existing string",
            "delete_string - Delete string and related details",
            "update_string_parent - Update string parent relationship"
        ],
        "String Detail Operations": [
            "create_string_detail - Create new string detail",
            "update_string_detail - Update existing string detail", 
            "delete_string_detail - Delete string detail"
        ],
        "Submission Operations": [
            "create_submission - Create new submission",
            "update_submission - Update existing submission",
            "delete_submission - Delete submission and related strings"
        ]
    }
    
    for category, operations in operation_types.items():
        print(f"\n{category}:")
        for operation in operations:
            print(f"  • {operation}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Multi-Operations Endpoint Examples")
    print("=====================================")
    
    # Show help
    get_operation_types_help()
    
    # Run examples
    try:
        # Example 1: The original use case (grouped array format)
        example_1_update_details_and_parent()
        
        # Example 1b: Same use case (individual format)
        example_1b_update_details_and_parent_individual()
        
        # Example 2: Complex string creation
        example_2_create_complex_string()
        
        # Example 3: Complex workflow
        example_3_complex_workflow()
        
        # Example 4: Bulk deletions
        example_4_bulk_delete()
        
        # Example 5: Bulk operations with arrays (NEW!)
        example_5_bulk_operations_with_arrays()
        
        # Example 6: Mixed operations
        example_5_mixed_operations()
        
        # Demonstrate rollback behavior
        demonstrate_rollback_behavior()
        
    except Exception as e:
        print(f"❌ Example execution failed: {str(e)}")
    
    print("\n✨ Examples completed!")
    print("\nKey Benefits of Multi-Operations Endpoint:")
    print("• Atomic transactions - all operations succeed or all fail")
    print("• Single API call for complex workflows")
    print("• Better performance than multiple sequential requests")
    print("• Consistent database state guaranteed")
    print("• Comprehensive validation before execution")
