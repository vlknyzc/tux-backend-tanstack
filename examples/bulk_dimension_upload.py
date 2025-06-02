#!/usr/bin/env python3
"""
Example script demonstrating bulk dimension and dimension value uploads.

This script shows how to use the bulk creation endpoints for dimensions
and dimension values, including error handling and validation.
"""

import requests
import json
from typing import List, Dict, Any


class DimensionBulkUploader:
    """Helper class for bulk uploading dimensions and dimension values."""

    def __init__(self, base_url: str, auth_token: str = None):
        """
        Initialize the uploader.

        Args:
            base_url: The base URL of the API (e.g., 'http://localhost:8000/api')
            auth_token: JWT token for authentication (optional for DEBUG mode)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            })
        else:
            self.session.headers.update({
                'Content-Type': 'application/json'
            })

    def bulk_create_dimensions(self, dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk create dimensions.

        Args:
            dimensions: List of dimension dictionaries

        Returns:
            Response from the API
        """
        url = f"{self.base_url}/dimensions/bulk_create/"
        data = {"dimensions": dimensions}

        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating dimensions: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(
                        f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error response: {e.response.text}")
            raise

    def bulk_create_dimension_values(self, dimension_values: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk create dimension values.

        Args:
            dimension_values: List of dimension value dictionaries

        Returns:
            Response from the API
        """
        url = f"{self.base_url}/dimension-values/bulk_create/"
        data = {"dimension_values": dimension_values}

        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating dimension values: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(
                        f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Error response: {e.response.text}")
            raise

    def get_dimensions(self) -> List[Dict[str, Any]]:
        """Get all dimensions for reference."""
        url = f"{self.base_url}/dimensions/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


def example_bulk_upload():
    """Example of how to use the bulk upload functionality."""

    # Initialize uploader (adjust URL as needed)
    uploader = DimensionBulkUploader('http://localhost:8000/api')

    # Example 1: Create dimensions
    print("Creating dimensions...")
    dimensions_data = [
        {
            "name": "Environment",
            "description": "Deployment environment (prod, dev, test)",
            "type": "list",
            "status": "active"
        },
        {
            "name": "Region",
            "description": "Geographic deployment region",
            "type": "list",
            "status": "active"
        },
        {
            "name": "Cost Center",
            "description": "Internal cost center code",
            "type": "list",
            "status": "active"
        },
        {
            "name": "Project Code",
            "description": "Project identifier for tracking",
            "type": "text",
            "status": "active"
        }
    ]

    try:
        result = uploader.bulk_create_dimensions(dimensions_data)
        print(f"✅ Successfully created {result['success_count']} dimensions")
        if result['error_count'] > 0:
            print(f"❌ {result['error_count']} dimensions failed:")
            for error in result['errors']:
                print(f"  - {error['dimension_name']}: {error['error']}")
        print()
    except Exception as e:
        print(f"Failed to create dimensions: {e}")
        return

    # Get created dimensions to use their IDs
    dimensions = uploader.get_dimensions()
    dimension_map = {dim['name']: dim['id'] for dim in dimensions}

    # Example 2: Create dimension values
    print("Creating dimension values...")

    # Environment values
    env_values = [
        {
            "dimension": dimension_map["Environment"],
            "value": "prod",
            "label": "Production",
            "utm": "prod",
            "description": "Production environment"
        },
        {
            "dimension": dimension_map["Environment"],
            "value": "staging",
            "label": "Staging",
            "utm": "staging",
            "description": "Staging environment"
        },
        {
            "dimension": dimension_map["Environment"],
            "value": "dev",
            "label": "Development",
            "utm": "dev",
            "description": "Development environment"
        },
        {
            "dimension": dimension_map["Environment"],
            "value": "test",
            "label": "Testing",
            "utm": "test",
            "description": "Testing environment"
        }
    ]

    # Region values
    region_values = [
        {
            "dimension": dimension_map["Region"],
            "value": "us-east-1",
            "label": "US East (Virginia)",
            "utm": "use1",
            "description": "US East Virginia region"
        },
        {
            "dimension": dimension_map["Region"],
            "value": "us-west-2",
            "label": "US West (Oregon)",
            "utm": "usw2",
            "description": "US West Oregon region"
        },
        {
            "dimension": dimension_map["Region"],
            "value": "eu-west-1",
            "label": "EU West (Ireland)",
            "utm": "euw1",
            "description": "EU West Ireland region"
        }
    ]

    # Cost center values
    cost_center_values = [
        {
            "dimension": dimension_map["Cost Center"],
            "value": "IT001",
            "label": "IT Operations",
            "utm": "it001",
            "description": "IT Operations cost center"
        },
        {
            "dimension": dimension_map["Cost Center"],
            "value": "MKT001",
            "label": "Marketing",
            "utm": "mkt001",
            "description": "Marketing cost center"
        },
        {
            "dimension": dimension_map["Cost Center"],
            "value": "DEV001",
            "label": "Development",
            "utm": "dev001",
            "description": "Development cost center"
        }
    ]

    # Combine all dimension values
    all_dimension_values = env_values + region_values + cost_center_values

    try:
        result = uploader.bulk_create_dimension_values(all_dimension_values)
        print(
            f"✅ Successfully created {result['success_count']} dimension values")
        if result['error_count'] > 0:
            print(f"❌ {result['error_count']} dimension values failed:")
            for error in result['errors']:
                print(
                    f"  - {error['dimension_value']} (dimension {error['dimension_id']}): {error['error']}")
        print()
    except Exception as e:
        print(f"Failed to create dimension values: {e}")
        return

    print("🎉 Bulk upload completed successfully!")


def example_with_hierarchical_dimensions():
    """Example showing hierarchical dimensions with parent-child relationships."""

    uploader = DimensionBulkUploader('http://localhost:8000/api')

    print("Creating hierarchical dimensions...")

    # First, create parent dimensions
    parent_dimensions = [
        {
            "name": "Geographic Location",
            "description": "Top-level geographic categorization",
            "type": "list",
            "status": "active"
        },
        {
            "name": "Business Unit",
            "description": "Top-level business organization",
            "type": "list",
            "status": "active"
        }
    ]

    result = uploader.bulk_create_dimensions(parent_dimensions)
    print(f"Created {result['success_count']} parent dimensions")

    # Get dimensions to find parent IDs
    dimensions = uploader.get_dimensions()
    dimension_map = {dim['name']: dim['id'] for dim in dimensions}

    # Create child dimensions
    child_dimensions = [
        {
            "name": "Country",
            "description": "Country within geographic location",
            "type": "list",
            "status": "active",
            "parent": dimension_map["Geographic Location"]
        },
        {
            "name": "Department",
            "description": "Department within business unit",
            "type": "list",
            "status": "active",
            "parent": dimension_map["Business Unit"]
        }
    ]

    result = uploader.bulk_create_dimensions(child_dimensions)
    print(f"Created {result['success_count']} child dimensions")

    # Now create values for the hierarchical structure
    dimensions = uploader.get_dimensions()
    dimension_map = {dim['name']: dim['id'] for dim in dimensions}

    # Parent dimension values
    parent_values = [
        {
            "dimension": dimension_map["Geographic Location"],
            "value": "americas",
            "label": "Americas",
            "utm": "amer",
            "description": "North and South America"
        },
        {
            "dimension": dimension_map["Geographic Location"],
            "value": "emea",
            "label": "EMEA",
            "utm": "emea",
            "description": "Europe, Middle East, and Africa"
        },
        {
            "dimension": dimension_map["Business Unit"],
            "value": "engineering",
            "label": "Engineering",
            "utm": "eng",
            "description": "Engineering business unit"
        }
    ]

    result = uploader.bulk_create_dimension_values(parent_values)
    print(f"Created {result['success_count']} parent dimension values")

    # Get dimension values to use as parents
    all_dim_values = uploader.session.get(
        f"{uploader.base_url}/dimension-values/").json()
    value_map = {f"{val['dimension_name']}:{val['value']}": val['id']
                 for val in all_dim_values}

    # Child dimension values with parent relationships
    child_values = [
        {
            "dimension": dimension_map["Country"],
            "value": "us",
            "label": "United States",
            "utm": "us",
            "description": "United States of America",
            "parent": value_map["Geographic Location:americas"]
        },
        {
            "dimension": dimension_map["Country"],
            "value": "ca",
            "label": "Canada",
            "utm": "ca",
            "description": "Canada",
            "parent": value_map["Geographic Location:americas"]
        },
        {
            "dimension": dimension_map["Department"],
            "value": "backend",
            "label": "Backend Development",
            "utm": "be",
            "description": "Backend development team",
            "parent": value_map["Business Unit:engineering"]
        },
        {
            "dimension": dimension_map["Department"],
            "value": "frontend",
            "label": "Frontend Development",
            "utm": "fe",
            "description": "Frontend development team",
            "parent": value_map["Business Unit:engineering"]
        }
    ]

    result = uploader.bulk_create_dimension_values(child_values)
    print(f"Created {result['success_count']} child dimension values")

    print("🎉 Hierarchical bulk upload completed!")


if __name__ == "__main__":
    print("=== Dimension Bulk Upload Examples ===\n")

    print("Example 1: Basic bulk upload")
    example_bulk_upload()

    print("\n" + "="*50 + "\n")

    print("Example 2: Hierarchical dimensions")
    example_with_hierarchical_dimensions()

    print("\n=== Examples completed ===")
