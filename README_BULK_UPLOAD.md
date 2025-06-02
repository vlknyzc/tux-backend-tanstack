# Bulk Upload Feature for Dimensions and Dimension Values

This document describes the newly implemented bulk upload functionality for dimensions and dimension values in the TUX backend system.

## Overview

The bulk upload feature allows you to create multiple dimensions and dimension values in a single API request, with proper transaction handling and error reporting. This is especially useful for:

- Initial system setup
- Large-scale data migrations
- CSV-based data imports
- Batch operations

## New Endpoints

### Bulk Create Dimensions

**Endpoint:** `POST /api/dimensions/bulk_create/`

Creates multiple dimensions in a single transaction.

**Features:**

- ✅ Transaction safety (all or nothing)
- ✅ Individual error reporting
- ✅ Automatic slug generation
- ✅ Created_by field handling
- ✅ Validation for each dimension

### Bulk Create Dimension Values

**Endpoint:** `POST /api/dimension-values/bulk_create/`

Creates multiple dimension values in a single transaction.

**Features:**

- ✅ Transaction safety (all or nothing)
- ✅ Individual error reporting
- ✅ Parent-child relationship support
- ✅ Dimension existence validation
- ✅ Created_by field handling

## Request/Response Format

### Bulk Dimensions Request

```json
{
  "dimensions": [
    {
      "name": "Environment",
      "description": "Deployment environment",
      "type": "list",
      "status": "active",
      "parent": null
    },
    {
      "name": "Region",
      "description": "Geographic region",
      "type": "list",
      "status": "active",
      "parent": null
    }
  ]
}
```

### Bulk Dimension Values Request

```json
{
  "dimension_values": [
    {
      "dimension": 1,
      "value": "prod",
      "label": "Production",
      "utm": "prod",
      "description": "Production environment",
      "valid_from": "2023-01-01",
      "valid_until": null,
      "parent": null
    },
    {
      "dimension": 1,
      "value": "dev",
      "label": "Development",
      "utm": "dev",
      "description": "Development environment",
      "valid_from": "2023-01-01",
      "valid_until": null,
      "parent": null
    }
  ]
}
```

### Response Format

Both endpoints return the same response structure:

```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    // Array of successfully created objects
  ],
  "errors": [
    // Array of error objects for failed creations
    {
      "index": 1,
      "dimension_name": "Duplicate Name",
      "error": "UNIQUE constraint failed: master_data_dimension.name"
    }
  ]
}
```

## Usage Examples

### 1. Python Script Example

See `examples/bulk_dimension_upload.py` for a complete Python implementation:

```python
from examples.bulk_dimension_upload import DimensionBulkUploader

uploader = DimensionBulkUploader('http://localhost:8000/api')

# Create dimensions
dimensions = [
    {
        "name": "Environment",
        "description": "Deployment environment",
        "type": "list",
        "status": "active"
    }
]

result = uploader.bulk_create_dimensions(dimensions)
print(f"Created {result['success_count']} dimensions")
```

### 2. CSV-based Upload

See `examples/csv_bulk_upload.py` for CSV-based bulk uploads:

```python
from examples.csv_bulk_upload import CSVBulkUploader

uploader = CSVBulkUploader('http://localhost:8000/api')
dimensions = uploader.read_dimensions_csv('dimensions.csv')
result = uploader.bulk_create_dimensions(dimensions)
```

Expected CSV format for dimensions:

```csv
name,description,type,status,parent_name
Environment,Deployment environment,list,active,
Region,Geographic region,list,active,
```

Expected CSV format for dimension values:

```csv
dimension_name,value,label,utm,description,valid_from,valid_until,parent_value
Environment,prod,Production,prod,Production environment,2023-01-01,,
Environment,dev,Development,dev,Development environment,2023-01-01,,
```

### 3. cURL Example

```bash
# Bulk create dimensions
curl -X POST http://localhost:8000/api/dimensions/bulk_create/ \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [
      {
        "name": "Environment",
        "description": "Deployment environment",
        "type": "list",
        "status": "active"
      }
    ]
  }'

# Bulk create dimension values
curl -X POST http://localhost:8000/api/dimension-values/bulk_create/ \
  -H "Content-Type: application/json" \
  -d '{
    "dimension_values": [
      {
        "dimension": 1,
        "value": "prod",
        "label": "Production",
        "utm": "prod",
        "description": "Production environment"
      }
    ]
  }'
```

## Validation Rules

### Dimensions

- `name` (required): Must be unique
- `type` (required): Must be one of the valid DimensionTypeChoices
- `status` (optional): Must be one of the valid StatusChoices, defaults to "active"
- `description` (optional): Text description
- `parent` (optional): ID of parent dimension

### Dimension Values

- `dimension` (required): Must reference an existing dimension ID
- `value` (required): Must be unique within the dimension
- `label` (required): Human-readable label
- `utm` (required): UTM/tracking code
- `description` (optional): Text description
- `valid_from` (optional): Date field
- `valid_until` (optional): Date field
- `parent` (optional): ID of parent dimension value

## Error Handling

The bulk endpoints provide comprehensive error handling:

1. **Validation Errors**: Field-level validation with detailed messages
2. **Database Constraints**: Unique constraint violations, foreign key errors
3. **Transaction Safety**: If any item fails, the entire batch is rolled back
4. **Individual Error Reporting**: Each failed item is reported with its index and error message

## Best Practices

### 1. Batch Size

- Recommended batch size: 50-100 items per request
- For larger datasets, split into multiple batches

### 2. Error Handling

```python
result = uploader.bulk_create_dimensions(dimensions)

if result['error_count'] > 0:
    for error in result['errors']:
        print(f"Failed to create {error['dimension_name']}: {error['error']}")
```

### 3. Hierarchical Data

When creating hierarchical data:

1. Create parent dimensions first
2. Create child dimensions with parent references
3. Create parent dimension values
4. Create child dimension values with parent references

### 4. CSV Processing

- Always validate CSV data before uploading
- Handle encoding issues (use UTF-8)
- Trim whitespace from fields
- Validate required fields before API calls

## Testing

Run the example scripts to test the functionality:

```bash
# Basic bulk upload example
python examples/bulk_dimension_upload.py

# CSV-based upload example
python examples/csv_bulk_upload.py
```

## Performance Considerations

- Bulk operations are significantly faster than individual requests
- Database constraints are enforced efficiently
- Transaction overhead is minimized
- Memory usage scales linearly with batch size

## Security

- All existing authentication and authorization rules apply
- In production, authentication is required
- In debug mode, endpoints are publicly accessible for testing
- User context is preserved for created_by fields

## Migration from Individual Requests

To migrate existing individual creation code:

**Before:**

```python
for dimension in dimensions:
    response = requests.post('/api/dimensions/', json=dimension)
```

**After:**

```python
response = requests.post('/api/dimensions/bulk_create/',
                        json={'dimensions': dimensions})
```

## Future Enhancements

Potential future improvements:

- Bulk update functionality
- Bulk delete functionality
- Excel file support
- Async processing for very large batches
- Progress tracking for long-running operations

## Support

For questions or issues with the bulk upload functionality:

1. Check the API documentation
2. Review the example scripts
3. Verify your data format and validation rules
4. Contact the backend development team
