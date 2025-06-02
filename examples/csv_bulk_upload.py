#!/usr/bin/env python3
"""
CSV-based bulk upload example for dimensions and dimension values.

This script demonstrates how to read CSV files and use them for bulk uploads.
Now supports name-based references for parent dimensions and values.
"""

import requests
import csv
import json
from pathlib import Path
from typing import List, Dict, Any


class CSVBulkUploader:
    """Helper class for CSV-based bulk uploads."""

    def __init__(self, base_url: str, auth_token: str = None):
        """Initialize the uploader."""
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

    def read_dimensions_csv(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """
        Read dimensions from CSV file.

        Expected CSV format:
        name,description,type,status,parent_name
        Environment,Deployment environment,list,active,
        Region,Geographic region,list,active,
        Subregion,Specific subregion,list,active,Region
        """
        dimensions = []

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                dimension = {
                    'name': row['name'].strip(),
                    'description': row['description'].strip(),
                    'type': row['type'].strip(),
                    'status': row['status'].strip() if row['status'] else 'active'
                }

                # Add parent_name if provided - the serializer will resolve it to ID
                if row.get('parent_name') and row['parent_name'].strip():
                    dimension['parent_name'] = row['parent_name'].strip()

                dimensions.append(dimension)

        return dimensions

    def read_dimension_values_csv(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """
        Read dimension values from CSV file.

        Expected CSV format:
        dimension_name,value,label,utm,description,valid_from,valid_until,parent_dimension_name,parent_value
        Environment,prod,Production,prod,Production environment,2023-01-01,,,
        Environment,dev,Development,dev,Development environment,2023-01-01,,,
        Region,us-east,US East,use,US East region,2023-01-01,,,
        Subregion,us-east-1,US East 1,use1,US East Virginia,2023-01-01,,Region,us-east
        """
        dimension_values = []

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                dim_value = {
                    'dimension_name': row['dimension_name'].strip(),
                    'value': row['value'].strip(),
                    'label': row['label'].strip(),
                    'utm': row['utm'].strip(),
                    'description': row['description'].strip() if row['description'] else '',
                }

                # Handle optional fields
                if row.get('valid_from') and row['valid_from'].strip():
                    dim_value['valid_from'] = row['valid_from'].strip()

                if row.get('valid_until') and row['valid_until'].strip():
                    dim_value['valid_until'] = row['valid_until'].strip()

                # Handle parent references by name - the serializer will resolve to IDs
                if (row.get('parent_dimension_name') and row.get('parent_value') and
                        row['parent_dimension_name'].strip() and row['parent_value'].strip()):
                    dim_value['parent_dimension_name'] = row['parent_dimension_name'].strip(
                    )
                    dim_value['parent_value'] = row['parent_value'].strip()

                dimension_values.append(dim_value)

        return dimension_values

    def bulk_create_dimensions(self, dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk create dimensions - now handles name-based parent references automatically."""
        url = f"{self.base_url}/dimensions/bulk_create/"
        data = {"dimensions": dimensions}

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def bulk_create_dimension_values(self, dimension_values: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk create dimension values - now handles name-based references automatically."""
        url = f"{self.base_url}/dimension-values/bulk_create/"
        data = {"dimension_values": dimension_values}

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()


def create_sample_csv_files():
    """Create sample CSV files for demonstration."""

    # Create dimensions CSV with parent relationships
    dimensions_csv = """name,description,type,status,parent_name
Environment,Deployment environment,list,active,
Region,Geographic deployment region,list,active,
Cost Center,Internal cost center code,list,active,
Project Code,Project identifier for tracking,text,active,
Subregion,Specific subregion within region,list,active,Region
Environment Type,Type within environment,list,active,Environment"""

    with open('sample_dimensions.csv', 'w', encoding='utf-8') as f:
        f.write(dimensions_csv)

    # Create dimension values CSV with name-based references
    dimension_values_csv = """dimension_name,value,label,utm,description,valid_from,valid_until,parent_dimension_name,parent_value
Environment,prod,Production,prod,Production environment,2023-01-01,,,
Environment,staging,Staging,staging,Staging environment,2023-01-01,,,
Environment,dev,Development,dev,Development environment,2023-01-01,,,
Environment,test,Testing,test,Testing environment,2023-01-01,,,
Environment Type,web,Web Server,web,Web server environment,2023-01-01,,Environment,prod
Environment Type,api,API Server,api,API server environment,2023-01-01,,Environment,prod
Environment Type,db,Database,db,Database environment,2023-01-01,,Environment,prod
Region,us-east,US East,use,US East region,2023-01-01,,,
Region,us-west,US West,usw,US West region,2023-01-01,,,
Region,eu-west,EU West,euw,EU West region,2023-01-01,,,
Subregion,us-east-1,US East 1,use1,US East Virginia,2023-01-01,,Region,us-east
Subregion,us-east-2,US East 2,use2,US East Ohio,2023-01-01,,Region,us-east
Subregion,us-west-1,US West 1,usw1,US West California,2023-01-01,,Region,us-west
Subregion,us-west-2,US West 2,usw2,US West Oregon,2023-01-01,,Region,us-west
Cost Center,IT001,IT Operations,it001,IT Operations cost center,,,
Cost Center,MKT001,Marketing,mkt001,Marketing cost center,,,
Cost Center,DEV001,Development,dev001,Development cost center,,,"""

    with open('sample_dimension_values.csv', 'w', encoding='utf-8') as f:
        f.write(dimension_values_csv)

    print("✅ Created sample CSV files:")
    print("  - sample_dimensions.csv (with parent_name references)")
    print("  - sample_dimension_values.csv (with name-based parent references)")


def main():
    """Main function demonstrating CSV bulk upload with name-based references."""

    print("=== CSV Bulk Upload with Name-Based References ===\n")

    # Create sample files
    create_sample_csv_files()

    # Initialize uploader
    uploader = CSVBulkUploader('http://localhost:8000/api')

    try:
        # Step 1: Upload dimensions from CSV (with automatic parent resolution)
        print("\nStep 1: Reading and uploading dimensions from CSV...")
        dimensions = uploader.read_dimensions_csv('sample_dimensions.csv')
        print(f"Read {len(dimensions)} dimensions from CSV")

        # The backend now handles parent name resolution automatically
        result = uploader.bulk_create_dimensions(dimensions)
        print(f"✅ Created {result['success_count']} dimensions")
        if result['error_count'] > 0:
            print(f"❌ {result['error_count']} failed:")
            for error in result['errors']:
                print(f"  - {error}")

        # Step 2: Upload dimension values from CSV (with automatic reference resolution)
        print("\nStep 2: Reading and uploading dimension values from CSV...")
        dimension_values = uploader.read_dimension_values_csv(
            'sample_dimension_values.csv')
        print(f"Read {len(dimension_values)} dimension values from CSV")

        # The backend now handles all name-based reference resolution automatically
        result = uploader.bulk_create_dimension_values(dimension_values)
        print(
            f"✅ Successfully created {result['success_count']} dimension values")
        if result['error_count'] > 0:
            print(f"❌ {result['error_count']} failed:")
            for error in result['errors']:
                print(f"  - {error}")

        print("\n🎉 CSV bulk upload with name-based references completed successfully!")
        print("\n📝 Key improvements:")
        print("  - No need to manually resolve dimension IDs")
        print("  - Parent dimensions can be referenced by name")
        print("  - Parent dimension values can be referenced by dimension_name:value")
        print("  - Automatic dependency handling for dimensions created in same batch")

    except Exception as e:
        print(f"❌ Error during bulk upload: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up sample files
        try:
            Path('sample_dimensions.csv').unlink()
            Path('sample_dimension_values.csv').unlink()
            print("\n🧹 Cleaned up sample CSV files")
        except:
            pass


if __name__ == "__main__":
    main()
