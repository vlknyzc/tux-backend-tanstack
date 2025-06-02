# Frontend Integration Guide: Bulk Upload with Name-Based References

## Overview

Enhanced bulk creation endpoints now support **name-based references** for parent dimensions and dimension values, making CSV uploads much more user-friendly. Users no longer need to know internal IDs - they can reference parents by name.

## Key Improvements

✅ **Name-based parent references** - Use dimension names instead of IDs  
✅ **Automatic dependency resolution** - Backend handles creation order  
✅ **Cross-batch references** - Parents can be in existing data or same batch  
✅ **Comprehensive validation** - Clear error messages for invalid references

## API Specifications

### Enhanced Bulk Dimensions Request

```typescript
interface BulkDimensionsRequest {
  dimensions: Array<{
    name: string; // Required: Unique dimension name
    description?: string; // Optional: Description text
    type: "list" | "text"; // Required: Dimension type
    status?: "active" | "inactive"; // Optional: defaults to 'active'

    // ID-based reference (existing)
    parent?: number; // Optional: Parent dimension ID

    // OR name-based reference (NEW)
    parent_name?: string; // Optional: Parent dimension name
  }>;
}
```

### Enhanced Bulk Dimension Values Request

```typescript
interface BulkDimensionValuesRequest {
  dimension_values: Array<{
    value: string; // Required: Value (must be unique within dimension)
    label: string; // Required: Human-readable label
    utm: string; // Required: UTM/tracking code
    description?: string; // Optional: Description
    valid_from?: string; // Optional: Date string (YYYY-MM-DD)
    valid_until?: string; // Optional: Date string (YYYY-MM-DD)

    // Dimension reference (choose one)
    dimension?: number; // Option 1: Dimension ID
    dimension_name?: string; // Option 2: Dimension name (NEW)

    // Parent reference (choose one)
    parent?: number; // Option 1: Parent dimension value ID

    // OR name-based parent reference (NEW)
    parent_dimension_name?: string; // Option 2a: Parent's dimension name
    parent_value?: string; // Option 2b: Parent's value
  }>;
}
```

## CSV Upload Formats

### Dimensions CSV

```csv
name,description,type,status,parent_name
Environment,Deployment environment,list,active,
Region,Geographic region,list,active,
Subregion,Specific subregion,list,active,Region
Environment Type,Type within environment,list,active,Environment
```

**Key Points:**

- `parent_name` column references parent dimensions by name
- Parent dimensions can be in existing data or same CSV batch
- Backend automatically handles creation order

### Dimension Values CSV

```csv
dimension_name,value,label,utm,description,valid_from,valid_until,parent_dimension_name,parent_value
Environment,prod,Production,prod,Production environment,2023-01-01,,,
Environment,staging,Staging,staging,Staging environment,2023-01-01,,,
Region,us-east,US East,use,US East region,2023-01-01,,,
Subregion,us-east-1,US East 1,use1,US East Virginia,2023-01-01,,Region,us-east
Environment Type,web,Web Server,web,Web server environment,2023-01-01,,Environment,prod
```

**Key Points:**

- `dimension_name` references the dimension by name
- `parent_dimension_name` + `parent_value` together reference the parent
- All references resolved automatically by backend

## Frontend Implementation

### Updated CSV Validators

```typescript
export function validateDimensionRow(row: any) {
  if (!row.name?.trim()) throw new Error("Name is required");
  if (!row.type?.trim()) throw new Error("Type is required");

  const dimension: any = {
    name: row.name.trim(),
    description: row.description?.trim() || "",
    type: row.type.trim(),
    status: row.status?.trim() || "active",
  };

  // Add parent reference if provided
  if (row.parent_name?.trim()) {
    dimension.parent_name = row.parent_name.trim();
  }

  return dimension;
}

export function validateDimensionValueRow(row: any) {
  if (!row.value?.trim()) throw new Error("Value is required");
  if (!row.label?.trim()) throw new Error("Label is required");
  if (!row.utm?.trim()) throw new Error("UTM is required");

  const dimValue: any = {
    value: row.value.trim(),
    label: row.label.trim(),
    utm: row.utm.trim(),
    description: row.description?.trim() || "",
  };

  // Dimension reference (prefer name over ID)
  if (row.dimension_name?.trim()) {
    dimValue.dimension_name = row.dimension_name.trim();
  } else if (row.dimension) {
    dimValue.dimension = parseInt(row.dimension);
  } else {
    throw new Error("Either dimension_name or dimension ID is required");
  }

  // Optional date fields
  if (row.valid_from?.trim()) dimValue.valid_from = row.valid_from.trim();
  if (row.valid_until?.trim()) dimValue.valid_until = row.valid_until.trim();

  // Parent reference (name-based)
  if (row.parent_dimension_name?.trim() && row.parent_value?.trim()) {
    dimValue.parent_dimension_name = row.parent_dimension_name.trim();
    dimValue.parent_value = row.parent_value.trim();
  }

  return dimValue;
}
```

### Simplified Upload Service

```typescript
class BulkUploadService {
  private baseUrl = "/api";

  async bulkCreateDimensions(dimensions: any[]) {
    // No preprocessing needed - backend handles name resolution
    const response = await fetch(`${this.baseUrl}/dimensions/bulk_create/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dimensions }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async bulkCreateDimensionValues(dimensionValues: any[]) {
    // No preprocessing needed - backend handles all reference resolution
    const response = await fetch(
      `${this.baseUrl}/dimension-values/bulk_create/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dimension_values: dimensionValues }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }
}
```

### Enhanced Error Handling

```typescript
interface NamedReferenceError {
  index: number;
  error: string;
  dimension_name?: string;
  parent_name?: string;
  dimension_value?: string;
  parent_dimension_name?: string;
  parent_value?: string;
}

function categorizeErrors(errors: NamedReferenceError[]) {
  const categories = {
    validation: [] as NamedReferenceError[],
    missing_parent: [] as NamedReferenceError[],
    missing_dimension: [] as NamedReferenceError[],
    duplicate: [] as NamedReferenceError[],
    other: [] as NamedReferenceError[],
  };

  errors.forEach((error) => {
    if (error.error.includes("not found")) {
      if (error.error.includes("Parent dimension")) {
        categories.missing_parent.push(error);
      } else if (error.error.includes("Dimension")) {
        categories.missing_dimension.push(error);
      } else {
        categories.other.push(error);
      }
    } else if (error.error.includes("UNIQUE constraint")) {
      categories.duplicate.push(error);
    } else if (error.error.includes("required")) {
      categories.validation.push(error);
    } else {
      categories.other.push(error);
    }
  });

  return categories;
}
```

### User-Friendly Error Display

```typescript
export function BulkUploadErrors({
  errors,
  originalData,
}: {
  errors: any[];
  originalData: any[];
}) {
  const categorizedErrors = categorizeErrors(errors);

  return (
    <div className="bulk-upload-errors">
      <h3>Upload Errors ({errors.length})</h3>

      {categorizedErrors.missing_parent.length > 0 && (
        <div className="error-category">
          <h4>
            Missing Parent References ({categorizedErrors.missing_parent.length})
          </h4>
          <p>
            These items reference parent dimensions/values that don't exist:
          </p>
          {categorizedErrors.missing_parent.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Row {error.index + 1}:</strong> {error.error}
              <div className="suggestion">
                💡 Ensure parent dimensions are created first or included in the
                same upload
              </div>
            </div>
          ))}
        </div>
      )}

      {categorizedErrors.missing_dimension.length > 0 && (
        <div className="error-category">
          <h4>
            Missing Dimension References (
            {categorizedErrors.missing_dimension.length})
          </h4>
          <p>These dimension values reference dimensions that don't exist:</p>
          {categorizedErrors.missing_dimension.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Row {error.index + 1}:</strong> {error.error}
              <div className="suggestion">
                💡 Create the dimension first or check the dimension name
                spelling
              </div>
            </div>
          ))}
        </div>
      )}

      {categorizedErrors.duplicate.length > 0 && (
        <div className="error-category">
          <h4>Duplicate Values ({categorizedErrors.duplicate.length})</h4>
          <p>These items have names/values that already exist:</p>
          {categorizedErrors.duplicate.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Row {error.index + 1}:</strong> {error.error}
              <div className="suggestion">
                💡 Use a different name/value or update the existing record
                instead
              </div>
            </div>
          ))}
        </div>
      )}

      {categorizedErrors.validation.length > 0 && (
        <div className="error-category">
          <h4>Validation Errors ({categorizedErrors.validation.length})</h4>
          {categorizedErrors.validation.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Row {error.index + 1}:</strong> {error.error}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## CSV Template Generation

### Generate Templates with Examples

```typescript
export function generateDimensionCSVTemplate(): string {
  const headers = ["name", "description", "type", "status", "parent_name"];
  const examples = [
    ["Environment", "Deployment environment", "list", "active", ""],
    ["Region", "Geographic region", "list", "active", ""],
    ["Subregion", "Specific subregion", "list", "active", "Region"],
    [
      "Environment Type",
      "Type within environment",
      "list",
      "active",
      "Environment",
    ],
  ];

  const csv = [headers, ...examples]
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  return csv;
}

export function generateDimensionValueCSVTemplate(): string {
  const headers = [
    "dimension_name",
    "value",
    "label",
    "utm",
    "description",
    "valid_from",
    "valid_until",
    "parent_dimension_name",
    "parent_value",
  ];

  const examples = [
    [
      "Environment",
      "prod",
      "Production",
      "prod",
      "Production environment",
      "2023-01-01",
      "",
      "",
      "",
    ],
    [
      "Environment",
      "dev",
      "Development",
      "dev",
      "Development environment",
      "2023-01-01",
      "",
      "",
      "",
    ],
    [
      "Region",
      "us-east",
      "US East",
      "use",
      "US East region",
      "2023-01-01",
      "",
      "",
      "",
    ],
    [
      "Subregion",
      "us-east-1",
      "US East 1",
      "use1",
      "US East Virginia",
      "2023-01-01",
      "",
      "Region",
      "us-east",
    ],
    [
      "Environment Type",
      "web",
      "Web Server",
      "web",
      "Web server environment",
      "2023-01-01",
      "",
      "Environment",
      "prod",
    ],
  ];

  const csv = [headers, ...examples]
    .map((row) => row.map((cell) => `"${cell}"`).join(","))
    .join("\n");

  return csv;
}
```

### Template Download Component

```typescript
export function CSVTemplateDownloader() {
  const downloadTemplate = (type: "dimensions" | "dimension-values") => {
    const csv =
      type === "dimensions"
        ? generateDimensionCSVTemplate()
        : generateDimensionValueCSVTemplate();

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `${type}-template.csv`;
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="csv-templates">
      <h3>CSV Templates</h3>
      <p>
        Download these templates to see the correct format and example data:
      </p>

      <div className="template-buttons">
        <button onClick={() => downloadTemplate("dimensions")}>
          📄 Download Dimensions Template
        </button>
        <button onClick={() => downloadTemplate("dimension-values")}>
          📄 Download Dimension Values Template
        </button>
      </div>

      <div className="template-info">
        <h4>Key Features:</h4>
        <ul>
          <li>✅ Use dimension names instead of IDs</li>
          <li>✅ Reference parent dimensions by name</li>
          <li>✅ Reference parent values by dimension_name:value</li>
          <li>✅ Automatic dependency resolution</li>
          <li>✅ Batch creation support</li>
        </ul>
      </div>
    </div>
  );
}
```

## Migration Guide

### From ID-based to Name-based

**Old Way (ID-based):**

```typescript
// Had to manually resolve IDs
const dimensionMap = await getDimensionsMap();
const resolvedData = data.map((item) => ({
  ...item,
  dimension: dimensionMap[item.dimension_name],
  parent: parentMap[item.parent_name],
}));
```

**New Way (Name-based):**

```typescript
// Backend handles resolution automatically
const result = await bulkCreateDimensionValues(data);
```

### Updating Existing CSV Processors

1. **Add new columns** to CSV templates:

   - `parent_name` for dimensions
   - `dimension_name`, `parent_dimension_name`, `parent_value` for dimension values

2. **Update validators** to handle name-based fields

3. **Remove manual resolution logic** - backend now handles this

4. **Update error handling** for new error types

## User Experience Improvements

### Progressive Enhancement

```typescript
export function BulkUploadWizard() {
  const [step, setStep] = useState(1);
  const [uploadType, setUploadType] = useState<"dimensions" | "values">(
    "dimensions"
  );

  return (
    <div className="bulk-upload-wizard">
      {step === 1 && (
        <div className="step-selection">
          <h2>What would you like to upload?</h2>
          <div className="upload-options">
            <button
              className={uploadType === "dimensions" ? "selected" : ""}
              onClick={() => setUploadType("dimensions")}
            >
              📁 Dimensions
              <small>Categories and hierarchies</small>
            </button>
            <button
              className={uploadType === "values" ? "selected" : ""}
              onClick={() => setUploadType("values")}
            >
              📋 Dimension Values
              <small>Specific values within dimensions</small>
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="template-step">
          <h2>Download Template</h2>
          <p>Use our template to ensure correct formatting:</p>
          <CSVTemplateDownloader />

          <div className="name-reference-info">
            <h3>✨ New: Name-Based References</h3>
            <p>You can now reference parent items by name instead of ID:</p>
            <ul>
              <li>
                Use <code>parent_name</code> for parent dimensions
              </li>
              <li>
                Use <code>dimension_name</code> instead of dimension ID
              </li>
              <li>
                Use <code>parent_dimension_name</code> +{" "}
                <code>parent_value</code> for parent values
              </li>
            </ul>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="upload-step">
          <CSVUpload
            onUpload={handleUpload}
            validator={
              uploadType === "dimensions"
                ? validateDimensionRow
                : validateDimensionValueRow
            }
            showPreview={true}
          />
        </div>
      )}
    </div>
  );
}
```

## Summary

The enhanced bulk upload system now provides:

- **User-friendly CSV uploads** with name-based references
- **Automatic dependency resolution** for complex hierarchies
- **Comprehensive error handling** with actionable feedback
- **Backward compatibility** with existing ID-based workflows
- **Simplified frontend code** with less manual processing

This significantly improves the user experience for bulk data imports while maintaining robust validation and error handling.
