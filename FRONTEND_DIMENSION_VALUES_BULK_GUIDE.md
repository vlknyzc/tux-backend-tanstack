# Frontend Guide: Dimension Values Bulk Upload

## Overview

This guide focuses specifically on implementing bulk upload functionality for **dimension values** in your frontend application. The enhanced API supports name-based references, making CSV uploads intuitive and user-friendly.

## Key Features

✅ **Name-based dimension references** - Use dimension names instead of IDs  
✅ **Name-based parent references** - Reference parent values by dimension_name:value  
✅ **Automatic reference resolution** - Backend handles all ID lookups  
✅ **Transaction safety** - All-or-nothing approach with individual error reporting  
✅ **CSV-friendly format** - Perfect for spreadsheet imports

## API Specification

### Endpoint

```
POST /api/dimension-values/bulk_create/
```

### Request Format

```typescript
interface BulkDimensionValuesRequest {
  dimension_values: Array<{
    // Required fields
    value: string; // Must be unique within dimension
    label: string; // Human-readable label
    utm: string; // UTM/tracking code

    // Optional fields
    description?: string; // Description text
    valid_from?: string; // Date string (YYYY-MM-DD)
    valid_until?: string; // Date string (YYYY-MM-DD)

    // Dimension reference (choose one approach)
    dimension?: number; // Option 1: Dimension ID (legacy)
    dimension_name?: string; // Option 2: Dimension name (recommended)

    // Parent reference (optional, choose one approach)
    parent?: number; // Option 1: Parent dimension value ID (legacy)

    // OR name-based parent reference (recommended)
    parent_dimension_name?: string; // Parent's dimension name
    parent_value?: string; // Parent's value
  }>;
}
```

### Response Format

```typescript
interface BulkDimensionValuesResponse {
  success_count: number;
  error_count: number;
  results: DimensionValue[]; // Successfully created dimension values
  errors: Array<{
    index: number; // Row index that failed
    dimension_value: string; // Value that failed
    dimension_id: string | number; // Dimension context
    error: string; // Error message
  }>;
}
```

## CSV Format

### Basic CSV Structure

```csv
dimension_name,value,label,utm,description,valid_from,valid_until,parent_dimension_name,parent_value
Environment,prod,Production,prod,Production environment,2023-01-01,,,
Environment,staging,Staging,staging,Staging environment,2023-01-01,,,
Region,us-east,US East,use,US East region,2023-01-01,,,
Subregion,us-east-1,US East 1,use1,US East Virginia,2023-01-01,,Region,us-east
```

### CSV Column Descriptions

| Column                  | Required | Description                                 | Example                  |
| ----------------------- | -------- | ------------------------------------------- | ------------------------ |
| `dimension_name`        | ✅       | Name of the dimension this value belongs to | `Environment`            |
| `value`                 | ✅       | Unique value within the dimension           | `prod`                   |
| `label`                 | ✅       | Human-readable display name                 | `Production`             |
| `utm`                   | ✅       | UTM/tracking code                           | `prod`                   |
| `description`           | ❌       | Optional description                        | `Production environment` |
| `valid_from`            | ❌       | Start date (YYYY-MM-DD)                     | `2023-01-01`             |
| `valid_until`           | ❌       | End date (YYYY-MM-DD)                       | `2024-12-31`             |
| `parent_dimension_name` | ❌       | Parent's dimension name                     | `Region`                 |
| `parent_value`          | ❌       | Parent's value                              | `us-east`                |

## Frontend Implementation

### 1. CSV Validation Function

```typescript
export interface DimensionValueRow {
  dimension_name: string;
  value: string;
  label: string;
  utm: string;
  description?: string;
  valid_from?: string;
  valid_until?: string;
  parent_dimension_name?: string;
  parent_value?: string;
}

export function validateDimensionValueRow(row: any): DimensionValueRow {
  // Validate required fields
  if (!row.value?.trim()) {
    throw new Error("Value is required");
  }
  if (!row.label?.trim()) {
    throw new Error("Label is required");
  }
  if (!row.utm?.trim()) {
    throw new Error("UTM is required");
  }

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
  if (row.valid_from?.trim()) {
    dimValue.valid_from = row.valid_from.trim();
  }
  if (row.valid_until?.trim()) {
    dimValue.valid_until = row.valid_until.trim();
  }

  // Parent reference (both fields required if using name-based approach)
  if (row.parent_dimension_name?.trim() || row.parent_value?.trim()) {
    if (!row.parent_dimension_name?.trim() || !row.parent_value?.trim()) {
      throw new Error(
        "Both parent_dimension_name and parent_value are required for parent reference"
      );
    }
    dimValue.parent_dimension_name = row.parent_dimension_name.trim();
    dimValue.parent_value = row.parent_value.trim();
  }

  return dimValue;
}
```

### 2. Upload Service

```typescript
class DimensionValueBulkUploadService {
  private baseUrl = "/api";

  async bulkCreateDimensionValues(dimensionValues: DimensionValueRow[]) {
    const response = await fetch(
      `${this.baseUrl}/dimension-values/bulk_create/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.getAuthToken()}`, // Add your auth logic
        },
        body: JSON.stringify({ dimension_values: dimensionValues }),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json() as BulkDimensionValuesResponse;
  }

  private getAuthToken(): string {
    // Implement your authentication logic here
    return localStorage.getItem("authToken") || "";
  }
}
```

### 3. CSV Processing Hook

```typescript
import { useState } from "react";
import Papa from "papaparse";

export function useDimensionValueCSVUpload() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<BulkDimensionValuesResponse | null>(
    null
  );
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const uploadService = new DimensionValueBulkUploadService();

  const processCSV = async (file: File) => {
    setIsProcessing(true);
    setValidationErrors([]);
    setResults(null);

    try {
      // Parse CSV
      const csvData = await new Promise<any[]>((resolve, reject) => {
        Papa.parse(file, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => resolve(results.data),
          error: (error) => reject(error),
        });
      });

      // Validate each row
      const validatedData: DimensionValueRow[] = [];
      const errors: string[] = [];

      csvData.forEach((row, index) => {
        try {
          const validatedRow = validateDimensionValueRow(row);
          validatedData.push(validatedRow);
        } catch (error) {
          errors.push(`Row ${index + 2}: ${error.message}`); // +2 for header and 0-index
        }
      });

      if (errors.length > 0) {
        setValidationErrors(errors);
        return;
      }

      // Upload to API
      const result = await uploadService.bulkCreateDimensionValues(
        validatedData
      );
      setResults(result);
    } catch (error) {
      setValidationErrors([`Upload failed: ${error.message}`]);
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    processCSV,
    isProcessing,
    results,
    validationErrors,
  };
}
```

### 4. Error Handling Component

```typescript
interface ErrorCategory {
  missing_dimension: any[];
  missing_parent: any[];
  duplicate: any[];
  validation: any[];
  other: any[];
}

function categorizeErrors(errors: any[]): ErrorCategory {
  const categories: ErrorCategory = {
    missing_dimension: [],
    missing_parent: [],
    duplicate: [],
    validation: [],
    other: [],
  };

  errors.forEach((error) => {
    if (
      error.error.includes("Dimension") &&
      error.error.includes("not found")
    ) {
      categories.missing_dimension.push(error);
    } else if (
      error.error.includes("Parent value") &&
      error.error.includes("not found")
    ) {
      categories.missing_parent.push(error);
    } else if (
      error.error.includes("UNIQUE constraint") ||
      error.error.includes("already exists")
    ) {
      categories.duplicate.push(error);
    } else if (error.error.includes("required")) {
      categories.validation.push(error);
    } else {
      categories.other.push(error);
    }
  });

  return categories;
}

export function DimensionValueUploadErrors({ errors }: { errors: any[] }) {
  const categorizedErrors = categorizeErrors(errors);

  return (
    <div className="upload-errors">
      <h3>Upload Errors ({errors.length})</h3>

      {categorizedErrors.missing_dimension.length > 0 && (
        <div className="error-category error-category--missing-dimension">
          <h4>
            Missing Dimensions ({categorizedErrors.missing_dimension.length})
          </h4>
          <p>These dimension values reference dimensions that don't exist:</p>
          {categorizedErrors.missing_dimension.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Row {error.index + 1}:</strong> {error.error}
              <div className="error-suggestion">
                💡 Create the dimension first or check the dimension name
                spelling
              </div>
            </div>
          ))}
        </div>
      )}

      {categorizedErrors.missing_parent.length > 0 && (
        <div className="error-category error-category--missing-parent">
          <h4>
            Missing Parent Values ({categorizedErrors.missing_parent.length})
          </h4>
          <p>These values reference parent values that don't exist:</p>
          {categorizedErrors.missing_parent.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Row {error.index + 1}:</strong> {error.error}
              <div className="error-suggestion">
                💡 Ensure parent values are created first or check the parent
                reference
              </div>
            </div>
          ))}
        </div>
      )}

      {categorizedErrors.duplicate.length > 0 && (
        <div className="error-category error-category--duplicate">
          <h4>Duplicate Values ({categorizedErrors.duplicate.length})</h4>
          <p>These values already exist in their dimensions:</p>
          {categorizedErrors.duplicate.map((error, index) => (
            <div key={index} className="error-item">
              <strong>Row {error.index + 1}:</strong> {error.error}
              <div className="error-suggestion">
                💡 Use a different value or update the existing record instead
              </div>
            </div>
          ))}
        </div>
      )}

      {categorizedErrors.validation.length > 0 && (
        <div className="error-category error-category--validation">
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

### 5. Success Results Component

```typescript
export function DimensionValueUploadResults({
  results,
}: {
  results: BulkDimensionValuesResponse;
}) {
  return (
    <div className="upload-results">
      <div className="results-summary">
        <h3>Upload Complete</h3>
        <div className="summary-stats">
          <div className="stat stat--success">
            <span className="stat-number">{results.success_count}</span>
            <span className="stat-label">Successfully Created</span>
          </div>
          {results.error_count > 0 && (
            <div className="stat stat--error">
              <span className="stat-number">{results.error_count}</span>
              <span className="stat-label">Failed</span>
            </div>
          )}
        </div>
      </div>

      {results.results.length > 0 && (
        <div className="created-values">
          <h4>Created Dimension Values</h4>
          <div className="values-list">
            {results.results.slice(0, 10).map((value, index) => (
              <div key={index} className="value-item">
                <strong>{value.label}</strong> ({value.value})
                <span className="dimension-name">
                  in {value.dimension_name}
                </span>
              </div>
            ))}
            {results.results.length > 10 && (
              <div className="more-items">
                ... and {results.results.length - 10} more
              </div>
            )}
          </div>
        </div>
      )}

      {results.error_count > 0 && (
        <DimensionValueUploadErrors errors={results.errors} />
      )}
    </div>
  );
}
```

## CSV Template Generation

### Template Creator Function

```typescript
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
      "staging",
      "Staging",
      "staging",
      "Staging environment",
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

export function downloadDimensionValueTemplate() {
  const csv = generateDimensionValueCSVTemplate();
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = "dimension-values-template.csv";
  link.click();

  URL.revokeObjectURL(url);
}
```

### Template Download Component

```typescript
export function DimensionValueTemplateDownloader() {
  return (
    <div className="template-downloader">
      <div className="template-info">
        <h3>CSV Template</h3>
        <p>Download the template to see the correct format and example data:</p>

        <button
          onClick={downloadDimensionValueTemplate}
          className="download-button"
        >
          📄 Download Dimension Values Template
        </button>
      </div>

      <div className="template-features">
        <h4>Template Features:</h4>
        <ul>
          <li>✅ Use dimension names instead of IDs</li>
          <li>✅ Reference parent values by dimension_name:value</li>
          <li>✅ Includes all optional fields</li>
          <li>✅ Example data for different scenarios</li>
          <li>✅ Hierarchical value examples</li>
        </ul>
      </div>

      <div className="template-notes">
        <h4>Important Notes:</h4>
        <ul>
          <li>
            <strong>Required fields:</strong> dimension_name, value, label, utm
          </li>
          <li>
            <strong>Parent references:</strong> Use both parent_dimension_name
            AND parent_value together
          </li>
          <li>
            <strong>Dates:</strong> Use YYYY-MM-DD format
          </li>
          <li>
            <strong>Empty cells:</strong> Leave optional fields empty if not
            needed
          </li>
        </ul>
      </div>
    </div>
  );
}
```

## Complete Upload Component

```typescript
import React, { useState } from "react";

export function DimensionValueBulkUpload() {
  const [step, setStep] = useState<"template" | "upload" | "results">(
    "template"
  );
  const { processCSV, isProcessing, results, validationErrors } =
    useDimensionValueCSVUpload();

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setStep("upload");
    await processCSV(file);
    setStep("results");
  };

  const resetUpload = () => {
    setStep("template");
  };

  return (
    <div className="dimension-value-bulk-upload">
      <div className="upload-header">
        <h2>Bulk Upload Dimension Values</h2>
        <p>Upload multiple dimension values from a CSV file</p>
      </div>

      {step === "template" && (
        <div className="step-template">
          <DimensionValueTemplateDownloader />

          <div className="upload-section">
            <h3>Upload Your CSV</h3>
            <p>Once you've prepared your CSV file, upload it here:</p>

            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="file-input"
            />
          </div>
        </div>
      )}

      {step === "upload" && (
        <div className="step-upload">
          <div className="processing-indicator">
            <div className="spinner"></div>
            <p>Processing your dimension values...</p>
            {isProcessing && (
              <p>
                Please wait while we validate and create your dimension values.
              </p>
            )}
          </div>
        </div>
      )}

      {step === "results" && (
        <div className="step-results">
          {validationErrors.length > 0 ? (
            <div className="validation-errors">
              <h3>Validation Errors</h3>
              <p>Please fix these issues in your CSV and try again:</p>
              <ul>
                {validationErrors.map((error, index) => (
                  <li key={index} className="validation-error">
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          ) : results ? (
            <DimensionValueUploadResults results={results} />
          ) : null}

          <div className="results-actions">
            <button onClick={resetUpload} className="button-secondary">
              Upload Another File
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

## CSS Styling

```css
.dimension-value-bulk-upload {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.upload-header {
  text-align: center;
  margin-bottom: 2rem;
}

.template-downloader {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.download-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.download-button:hover {
  background: #0056b3;
}

.template-features,
.template-notes {
  margin-top: 1rem;
}

.template-features ul,
.template-notes ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.file-input {
  display: block;
  width: 100%;
  padding: 0.75rem;
  border: 2px dashed #ccc;
  border-radius: 4px;
  background: #f8f9fa;
  cursor: pointer;
}

.processing-indicator {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.upload-results {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
}

.results-summary {
  text-align: center;
  margin-bottom: 2rem;
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1rem;
}

.stat {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 2rem;
  font-weight: bold;
}

.stat--success .stat-number {
  color: #28a745;
}

.stat--error .stat-number {
  color: #dc3545;
}

.error-category {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #dc3545;
  background: #fff5f5;
}

.error-item {
  margin: 0.5rem 0;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
}

.error-suggestion {
  font-size: 0.9rem;
  color: #666;
  margin-top: 0.25rem;
}

.validation-errors {
  background: #fff5f5;
  border: 1px solid #feb2b2;
  border-radius: 4px;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.validation-error {
  color: #c53030;
  margin: 0.5rem 0;
}

.results-actions {
  text-align: center;
  margin-top: 2rem;
}

.button-secondary {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
}

.button-secondary:hover {
  background: #545b62;
}
```

## Usage Example

```typescript
import React from "react";
import { DimensionValueBulkUpload } from "./components/DimensionValueBulkUpload";

function App() {
  return (
    <div className="app">
      <h1>Data Management</h1>
      <DimensionValueBulkUpload />
    </div>
  );
}

export default App;
```

## Summary

This dedicated guide provides everything needed to implement dimension value bulk uploads:

- ✅ **API integration** with name-based references
- ✅ **CSV processing** with validation
- ✅ **Error handling** with categorization
- ✅ **User-friendly components** with progress indication
- ✅ **Template generation** with examples
- ✅ **Complete styling** for professional UI

The implementation simplifies the user experience by eliminating the need to manually resolve dimension IDs, while providing robust error handling and validation feedback.
