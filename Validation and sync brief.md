# String Registry - Feature Brief

## Executive Summary

A comprehensive string management system that validates naming strings across all entity types (accounts, campaigns, ad groups, creatives, etc.) against Tuxonomy naming rules and builds a centralized registry. This feature enables users to audit compliance, catalog their marketing entities, and establish platform ID mappings for future automation.

## Core Concept

When users upload naming strings with metadata, the system simultaneously:

1. Validates strings against taxonomy rules
2. Registers platform IDs for future integration
3. Matches against existing Tuxonomy-generated strings
4. Builds a searchable string catalog
5. Provides optimization recommendations

## Feature Architecture

### Primary Feature Name

**String Registry** - Central hub for all naming string management across entity types

### Sub-Features

1. **Import & Validate** - Upload and check strings from platforms
2. **Browse Catalog** - View all registered strings
3. **Platform Mapping** - Manage external ID relationships
4. **Compliance Reports** - Analytics and insights

## Detailed User Stories

### Core Workflows

#### Import & Validation

- **As a campaign manager**, I want to upload a CSV of 500 campaign names from Meta to check which ones follow our Q4 naming convention, so I can identify which campaigns need to be renamed
- **As a creative producer**, I want to paste 20 creative names I just made to validate them before uploading to TikTok, so I can avoid rejection from the compliance team
- **As an account manager**, I want to validate account naming structures across all our Google Ads MCC accounts, so I can ensure consistent hierarchy

#### Data Quality & Recovery

- **As a user uploading a file**, I want clear error messages when my CSV is malformed, so I can fix it without guessing what's wrong
- **As a user with incomplete data**, I want to proceed with validation even if platform IDs are missing, so I can at least check naming compliance
- **As a user who selected the wrong rule**, I want to re-validate the same strings with a different rule without re-uploading, so I can quickly correct my mistake

#### Catalog Management

- **As an operations lead**, I want to search all historical strings by keyword, platform, or date range, so I can audit our naming evolution
- **As a data analyst**, I want to export all strings with their platform IDs that match certain criteria, so I can build reporting dashboards
- **As a team lead**, I want to see which team members uploaded which strings, so I can track compliance by person

#### Platform Integration Prep

- **As a media buyer**, I want to register Meta campaign IDs alongside validated strings, so we can later push updates back to Meta
- **As a performance marketer**, I want to map parent-child relationships (Campaign → Ad Set → Ad), so I can maintain hierarchy in our registry
- **As an automation specialist**, I want to identify all external strings that don't exist in Tuxonomy yet, so I can bulk-import them

### Error Scenarios

#### File Upload Errors

- **As a user uploading a CSV**, when my file is missing required columns, I want to see which specific columns are missing and download a template, so I can fix it quickly
- **As a user uploading a large file**, when my file exceeds size limits, I want suggestions on how to split it, so I can proceed with validation
- **As a user with encoding issues**, when my file contains special characters, I want the system to auto-detect encoding or provide clear instructions

#### Data Validation Errors

- **As a user with malformed data**, when entity_type values don't match allowed options, I want to see all invalid values and what the valid options are
- **As a user with mismatched data**, when I select "Campaign" but upload ad-level strings, I want a warning before processing
- **As a user with duplicate strings**, I want to know which rows are duplicates and choose to validate unique only

#### Process Errors

- **As a user whose validation failed**, I want to download a partial results file with successful validations, so I don't lose all progress
- **As a user whose browser crashed**, I want to retrieve my last validation job when I return, so I don't have to start over
- **As a user who lost connection**, I want the validation to continue server-side and email me when complete

## Core Features

### 1. Input Methods

#### Required Fields

- **String**: The actual naming string to validate
- **Entity Type**: Account | Campaign | Ad Group | Ad Set | Ad | Creative | Audience (REQUIRED)
- **Platform**: Meta | Google Ads | TikTok | Amazon Ads | LinkedIn | Twitter (REQUIRED)

#### Optional Fields

- **External ID**: Platform-specific identifier (e.g., campaign_123)
- **Parent ID**: For hierarchy tracking (e.g., account_id for campaigns)
- **Created Date**: When the entity was created in platform
- **Created By**: Email or username of creator
- **Tags**: Custom labels for organization

#### Input Options

##### CSV Upload

```csv
string,entity_type,platform,external_id,parent_id,created_date,created_by
EMEA_BrandAwareness_Q4_2024_Video,campaign,meta,camp_123,acc_456,2024-10-01,john@company.com
Prospecting_Broad_18-35,ad_group,google_ads,adg_789,camp_123,2024-10-02,jane@company.com
BlackFriday_Hero_1080x1920,creative,tiktok,cre_012,,2024-10-03,creative@company.com
```

##### Multi-line Text Input

```
Format: string|entity_type|platform|external_id (simplified format)

EMEA_BrandAwareness_Q4_2024_Video|campaign|meta|camp_123
Prospecting_Broad|ad_group|google_ads|adg_789
BlackFriday_Hero|creative|tiktok|cre_012
```

### 2. Input Validation & Error Handling

#### File Validation

```markdown
## Upload Validation Steps

1. File Format Check

   - Accepted: CSV, TXT, TSV, XLSX
   - Max size: 10MB or 10,000 rows
   - Encoding: UTF-8, UTF-16, ASCII

2. Structure Validation

   - Required columns present
   - Column names match expected
   - Data types correct

3. Data Validation
   - Entity types are valid
   - Platforms are recognized
   - No critical data missing

Error Response Example:
┌─────────────────────────────────────────┐
│ ❌ File Validation Failed │
│ │
│ Issues Found: │
│ • Missing column: "entity_type" │
│ • Invalid platform: "Facebook" (row 3) │
│ Valid options: meta, google_ads... │
│ • Empty strings found: rows 45, 67, 89 │
│ │
│ [Download Template] [View Sample File] │
└─────────────────────────────────────────┘
```

#### Progressive Validation

```markdown
## Multi-Stage Validation

Stage 1: File Structure ✅

- All required columns present
- File format valid

Stage 2: Data Integrity ⚠️

- 480/500 rows have valid data
- 20 rows have issues [View Issues]

Stage 3: Rule Validation

- Proceed with valid rows? [Yes] [Fix First]
```

### 3. Validation Process

#### Smart Rule Selection

```markdown
## Rule Selection Interface

Entity Type: [Campaign ▼]
Platform: [Meta ▼]

Available Rules (filtered):
┌──────────────────────────────────────┐
│ 📋 EMEA Campaign Standard (Default) │
│ Pattern: {Region}_{Objective}_... │
│ Last used: 2 days ago │
│ │
│ 📋 Global Campaign Q4 │
│ Pattern: {Brand}_{Quarter}_... │
│ Last used: 1 week ago │
│ │
│ 💡 Auto-detect from strings │
└──────────────────────────────────────┘
```

#### Entity-Specific Constraints

```javascript
const ENTITY_CONSTRAINTS = {
  account: {
    max_length: 60,
    special_chars_allowed: false,
    hierarchy_level: 0,
  },
  campaign: {
    max_length: 100,
    special_chars_allowed: true,
    hierarchy_level: 1,
  },
  ad_group: {
    max_length: 80,
    special_chars_allowed: true,
    hierarchy_level: 2,
  },
  creative: {
    max_length: 125,
    special_chars_allowed: true,
    hierarchy_level: 3,
  },
};
```

### 4. Results & Error Recovery

#### Results Dashboard

```markdown
## Validation Results

### Summary

Total Processed: 500 strings
✅ Passed: 380 (76%)
⚠️ Warnings: 80 (16%)
❌ Failed: 40 (8%)

### Quick Actions

[Export All] [Export Failures] [Re-validate Failed] [Save to Catalog]

### Filters

Entity Type: [All ▼]
Status: [All ▼]
Platform: [All ▼]
Date Range: [Last 7 days ▼]
```

#### Error Recovery Options

```markdown
## Failed Validation Recovery

40 strings failed validation. What would you like to do?

□ Download failure report with detailed errors
□ Auto-generate corrected versions
□ Re-validate with different rule
□ Save as draft for later review
□ Submit for manual review

[Take Action] [Skip]
```

#### Detailed Error Breakdown

```markdown
## String Analysis: "emea-brand-awareness_Q5-2024_static"

❌ 4 Issues Found:

1. Invalid Delimiter Mix
   Found: "-" and "_"
   Expected: "_" only
   Fix: Replace all "-" with "\_"

2. Invalid Quarter Value
   Found: "Q5"
   Valid: Q1, Q2, Q3, Q4
   Fix: Change to Q4

3. Case Mismatch
   Found: "emea" (lowercase)
   Expected: "EMEA" (uppercase)
   Fix: Convert to uppercase

4. Non-standard Format Value
   Found: "static"
   Suggestion: "Static" or "IMAGE"

[Apply All Fixes] [Apply Selected] [Edit Manually]
```

### 5. Registry Management

#### Search & Filter Interface

```markdown
## String Catalog

Search: [_____________] 🔍

### Active Filters

Platform: Meta ✕
Entity: Campaign ✕
Date: Last 30 days ✕
Status: Compliant ✕

### Results (1,847 strings)

| String             | Entity   | Platform | External ID | Status | Created | Actions       |
| ------------------ | -------- | -------- | ----------- | ------ | ------- | ------------- |
| EMEA_Brand_Q4_2024 | Campaign | Meta     | c_123       | ✅     | Oct 1   | [View] [Edit] |
| NA_Perf_Q4_2024    | Campaign | Google   | c_456       | ✅     | Oct 1   | [View] [Edit] |
| Creative_BF_Hero   | Creative | TikTok   | -           | ⚠️     | Oct 2   | [View] [Fix]  |

[Load More]
```

### 6. Export & Reporting

#### Export Configuration

```markdown
## Export Settings

### Format

○ CSV (Recommended)
○ Excel (.xlsx)
○ JSON
○ Google Sheets

### Include Data

☑ Validation results
☑ Platform mappings
☑ Error details
☑ Suggestions
☑ Metadata (dates, users)
☐ Historical changes

### Filters

Status: [All ▼]
Date Range: [Custom ▼]
Entity Types: [Selected: Campaign, Ad Group ▼]

### Grouping

○ No grouping
● Group by platform
○ Group by entity type
○ Group by validation status

[Preview Export] [Download]
```

## Technical Specifications

### API Endpoints

```typescript
// Import and validate
POST /api/registry/import
{
  entity_type: string,
  platform: string,
  rule_id?: string, // Optional - can auto-detect
  auto_detect_rule?: boolean,
  entries: [
    {
      string: string,
      external_id?: string,
      parent_id?: string,
      metadata?: {
        created_date?: string,
        created_by?: string,
        tags?: string[]
      }
    }
  ]
}

// Retry failed validation
POST /api/registry/retry/{job_id}
{
  rule_id?: string, // Use different rule
  only_failed?: boolean // Only retry failed items
}

// Search catalog
GET /api/registry/search
{
  q?: string,
  entity_types?: string[],
  platforms?: string[],
  status?: string[],
  date_from?: string,
  date_to?: string,
  page?: number,
  limit?: number
}

// Bulk operations
POST /api/registry/bulk-action
{
  action: 'export' | 'delete' | 'update' | 'fix',
  string_ids: string[],
  options?: {
    export_format?: string,
    update_fields?: object,
    auto_fix?: boolean
  }
}
```

### Error Response Standards

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details: {
      file_errors?: FileError[];
      row_errors?: RowError[];
      validation_errors?: ValidationError[];
    };
    recovery_options: RecoveryOption[];
  };
}

interface FileError {
  type: "missing_column" | "invalid_format" | "encoding" | "size_exceeded";
  message: string;
  suggestion: string;
}

interface RowError {
  row_number: number;
  column: string;
  value: any;
  error: string;
  valid_options?: string[];
}

interface RecoveryOption {
  action: string;
  label: string;
  endpoint: string;
  requires_input?: boolean;
}
```

### Data Models

```typescript
interface StringRegistryEntry {
  id: string;
  string: string;
  normalized_string: string; // Lowercase for searching
  entity_type: EntityType;
  platform: Platform;
  external_id?: string;
  parent_id?: string;
  hierarchy_path?: string[]; // Full hierarchy

  // Validation
  validation_results: ValidationResult[];
  last_validation_date: Date;
  compliance_status:
    | "compliant"
    | "non_compliant"
    | "warning"
    | "not_validated";

  // Origin
  source: "tuxonomy" | "external" | "manual";
  tuxonomy_string_id?: string;

  // Metadata
  created_date: Date;
  created_by: string;
  updated_date: Date;
  updated_by: string;
  tags: string[];

  // Workspace
  workspace_id: string;
  is_active: boolean;
}

interface ValidationResult {
  id: string;
  rule_id: string;
  rule_name: string;
  validated_at: Date;
  status: "passed" | "failed" | "warning";
  score: number;
  segments: SegmentValidation[];
  constraints: ConstraintCheck[];
  suggestions: Suggestion[];
  auto_fixed_version?: string;
}
```

### Performance & Limits

```javascript
const SYSTEM_LIMITS = {
  file_upload: {
    max_size_mb: 10,
    max_rows: 10000,
    chunk_size: 50,
    timeout_seconds: 300,
  },
  validation: {
    concurrent_validations: 5,
    max_strings_per_job: 10000,
    cache_ttl_seconds: 3600,
  },
  search: {
    max_results: 1000,
    default_page_size: 50,
    max_export_rows: 50000,
  },
};
```

## UI/UX Requirements

### Navigation

- Main Menu: **Registry** (or **String Registry**)
- Sub-navigation: Import & Validate | Browse | Reports | Settings
- Quick actions: [+ Import] [🔍 Search] [📊 Reports]
- Icon: 📚 (Registry) or 🗂️ (Database)

### Error States & Messages

#### File Upload Errors

```markdown
❌ Upload Failed

Your file couldn't be processed:

- Column "entity_type" is missing
- Found 3 columns, expected at least 4

💡 Tip: Download our template to ensure your file has the correct format

[Download Template] [Try Again] [Get Help]
```

#### Validation Warnings

```markdown
⚠️ Validation Complete with Warnings

380 strings passed
80 strings have warnings (still usable)
40 strings failed validation

Common issues:

- 30 strings exceed recommended length
- 25 strings use deprecated patterns
- 25 strings have case inconsistencies

[View Details] [Export Report] [Fix Issues]
```

### Responsive Design

- **Mobile** (<768px): Single column, collapsible sections, swipe actions
- **Tablet** (768-1024px): Two-column layout, modal overlays
- **Desktop** (>1024px): Multi-column with side panels

### Accessibility Requirements

- **WCAG 2.1 AA Compliance**
- Keyboard navigation (Tab, Shift+Tab, Arrow keys)
- Screen reader announcements for status changes
- High contrast mode support
- Focus indicators on all interactive elements
- Error messages linked to form fields

## Success Metrics

### Adoption Metrics

- Daily active users
- Strings validated per week
- Registry growth rate
- Feature retention (% returning users)

### Quality Metrics

- Average compliance score
- Error resolution rate
- Time to validate (by batch size)
- Auto-fix success rate

### Business Impact

- Reduction in naming errors (%)
- Cross-platform reporting accuracy
- Time saved on audits (hours)
- Platform sync readiness (% with IDs)

## Implementation Phases

### MVP (Week 1-2)

✅ Basic upload and validation
✅ Required field validation
✅ Simple results display
✅ CSV export
✅ Error messages

### Phase 1 (Week 3-4)

📋 Advanced error handling
📋 Multi-entity support
📋 Registry search
📋 Bulk retry
📋 Template downloads

### Phase 2 (Month 2)

🎯 Auto-detect rules
🎯 String matching
🎯 Fix suggestions
🎯 Historical tracking
🎯 Advanced filters

### Phase 3 (Month 3)

🚀 Platform ID mapping
🚀 Hierarchy management
🚀 Team collaboration
🚀 API access
🚀 Analytics dashboard

## Security Considerations

### Data Protection

- Sanitize all input strings
- Validate file types and sizes
- Scan for malicious content
- Encrypt platform IDs at rest

### Access Control

- Workspace isolation
- Role-based permissions
- Audit logging
- Session management

### Rate Limiting

- 100 uploads per hour per user
- 10,000 validations per day per workspace
- 50 concurrent validations per workspace

## Dependencies

### Internal Systems

- User authentication service
- Dimension management system
- Rule engine
- File storage service
- Background job processor
- Email notification service

### External Services

- Cloud storage (for large exports)
- CDN (for template files)
- Analytics platform
