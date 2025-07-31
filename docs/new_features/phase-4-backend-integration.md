# Phase 4: Backend Integration - Developer Brief

## Overview

This document outlines the backend API endpoints and data structures needed to support the grid-builder update functionality. The frontend has been implemented for Phases 1-2 and now requires backend support for string updates with inheritance management.

## Core Requirements

### 1. String Update Operations
- Update existing strings while preserving inheritance relationships
- Batch update multiple strings atomically
- Track modification history and change attribution
- Validate inheritance constraints before applying updates

### 2. Inheritance Impact Analysis
- Calculate which child strings will be affected by parent updates
- Provide impact preview before committing changes
- Handle cascading inheritance updates automatically
- Prevent orphaned strings and broken inheritance chains

### 3. Conflict Resolution
- Detect and resolve conflicts when multiple users update related strings
- Handle inheritance conflicts when parent-child relationships change
- Provide rollback mechanisms for failed batch operations

## API Endpoints Required

### 1. String Update Endpoint

```http
PUT /api/workspaces/{workspaceId}/strings/batch-update
```

**Purpose**: Update multiple existing strings with inheritance management

**Request Body**:
```typescript
{
  "updates": [
    {
      "string_id": number,
      "field_updates": {
        "field_{field_item_id}": string | null,
        // ... other field updates
      },
      "metadata": {
        "original_string_uuid": string,
        "original_value": string,
        "modified_by": string,
        "modified_at": string,
        "change_reason": string?
      }
    }
  ],
  "options": {
    "validate_inheritance": boolean,
    "auto_update_children": boolean,
    "create_backup": boolean,
    "dry_run": boolean
  }
}
```

**Response**:
```typescript
{
  "success": boolean,
  "updated_strings": number[],
  "affected_strings": number[],
  "inheritance_updates": [
    {
      "string_id": number,
      "parent_string_id": number,
      "updated_fields": string[],
      "inherited_values": Record<string, string>
    }
  ],
  "conflicts": [
    {
      "string_id": number,
      "conflict_type": "inheritance" | "concurrent_edit" | "validation",
      "message": string,
      "suggested_resolution": string?
    }
  ],
  "backup_id": string?,
  "errors": [
    {
      "string_id": number,
      "field": string?,
      "message": string,
      "code": string
    }
  ]
}
```

### 2. Inheritance Impact Analysis Endpoint

```http
POST /api/workspaces/{workspaceId}/strings/analyze-impact
```

**Purpose**: Calculate inheritance impact before applying updates

**Request Body**:
```typescript
{
  "updates": [
    {
      "string_id": number,
      "field_updates": Record<string, string | null>
    }
  ],
  "depth": number // Maximum inheritance depth to analyze (default: 10)
}
```

**Response**:
```typescript
{
  "impact": {
    "direct_updates": number,
    "inheritance_updates": number,
    "total_affected": number,
    "max_depth": number
  },
  "affected_strings": [
    {
      "string_id": number,
      "string_value": string,
      "parent_string_id": number?,
      "level": number,
      "update_type": "direct" | "inherited",
      "affected_fields": string[],
      "new_values": Record<string, string>,
      "children": number[]
    }
  ],
  "warnings": [
    {
      "string_id": number,
      "warning_type": "deep_inheritance" | "many_children" | "circular_dependency",
      "message": string,
      "severity": "low" | "medium" | "high"
    }
  ],
  "blockers": [
    {
      "string_id": number,
      "blocker": "missing_parent" | "circular_reference" | "invalid_field",
      "message": string
    }
  ]
}
```

### 3. String History and Backup Endpoint

```http
GET /api/workspaces/{workspaceId}/strings/{stringId}/history
```

**Purpose**: Retrieve modification history for rollback functionality

**Response**:
```typescript
{
  "history": [
    {
      "id": string,
      "string_id": number,
      "version": number,
      "values": Record<string, string>,
      "string_value": string,
      "modified_by": string,
      "modified_at": string,
      "change_type": "direct_edit" | "inheritance_update" | "batch_update",
      "parent_version": string?,
      "metadata": {
        "change_reason": string?,
        "batch_id": string?,
        "affected_fields": string[]
      }
    }
  ]
}
```

### 4. Rollback Endpoint

```http
POST /api/workspaces/{workspaceId}/strings/rollback
```

**Purpose**: Rollback strings to previous versions

**Request Body**:
```typescript
{
  "rollback_type": "single" | "batch" | "backup",
  "target": {
    "string_id": number?, // For single rollback
    "version": number?, // For single rollback
    "batch_id": string?, // For batch rollback
    "backup_id": string? // For backup rollback
  },
  "options": {
    "rollback_children": boolean,
    "validate_inheritance": boolean
  }
}
```

## Database Schema Changes

### 1. String Modifications Table
```sql
CREATE TABLE string_modifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    string_id INTEGER NOT NULL REFERENCES strings(id),
    version INTEGER NOT NULL,
    field_updates JSONB NOT NULL,
    string_value TEXT NOT NULL,
    original_values JSONB NOT NULL,
    modified_by INTEGER NOT NULL REFERENCES users(id),
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_type VARCHAR(50) NOT NULL,
    batch_id UUID,
    parent_version UUID REFERENCES string_modifications(id),
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(string_id, version)
);

CREATE INDEX idx_string_modifications_string_id ON string_modifications(string_id);
CREATE INDEX idx_string_modifications_batch_id ON string_modifications(batch_id);
CREATE INDEX idx_string_modifications_modified_at ON string_modifications(modified_at);
```

### 2. String Inheritance Tracking Table
```sql
CREATE TABLE string_inheritance_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_modification_id UUID NOT NULL REFERENCES string_modifications(id),
    child_string_id INTEGER NOT NULL REFERENCES strings(id),
    inherited_fields JSONB NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(parent_modification_id, child_string_id)
);

CREATE INDEX idx_inheritance_updates_parent ON string_inheritance_updates(parent_modification_id);
CREATE INDEX idx_inheritance_updates_child ON string_inheritance_updates(child_string_id);
```

### 3. Update Batches Table
```sql
CREATE TABLE string_update_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id INTEGER NOT NULL REFERENCES workspaces(id),
    rule_id INTEGER NOT NULL REFERENCES rules(id),
    field_id INTEGER NOT NULL REFERENCES fields(id),
    initiated_by INTEGER NOT NULL REFERENCES users(id),
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_strings INTEGER NOT NULL,
    processed_strings INTEGER DEFAULT 0,
    failed_strings INTEGER DEFAULT 0,
    backup_id UUID,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_update_batches_workspace ON string_update_batches(workspace_id);
CREATE INDEX idx_update_batches_status ON string_update_batches(status);
```

## Business Logic Requirements

### 1. Inheritance Validation Rules
- **Field Compatibility**: Updated fields must be compatible with child string field configurations
- **Value Propagation**: Inherited fields in child strings must update automatically when parent changes
- **Circular Reference Prevention**: Prevent updates that would create circular inheritance
- **Orphan Prevention**: Ensure parent strings exist and are valid before allowing child updates

### 2. Concurrency Control
- **Optimistic Locking**: Use version numbers or timestamps to detect concurrent modifications
- **Batch Atomicity**: All updates in a batch must succeed or all must be rolled back
- **Inheritance Consistency**: Ensure inheritance updates happen atomically with parent updates

### 3. Validation Requirements
- **Field Value Validation**: Validate field values against dimension constraints (list values, text patterns)
- **Required Field Validation**: Ensure all required fields have values after updates
- **Inheritance Chain Validation**: Verify inheritance chains remain valid after updates
- **Duplicate Prevention**: Prevent updates that would create duplicate string values

### 4. Performance Considerations
- **Batch Processing**: Process large updates in chunks to avoid timeouts
- **Inheritance Caching**: Cache inheritance relationships to avoid repeated queries
- **Background Processing**: Consider async processing for large inheritance updates
- **Index Optimization**: Ensure proper indexing for inheritance traversal queries

## Error Handling

### 1. Validation Errors
```typescript
{
  "code": "VALIDATION_ERROR",
  "message": "Field validation failed",
  "details": {
    "string_id": number,
    "field": string,
    "value": string,
    "constraint": string,
    "allowed_values": string[]?
  }
}
```

### 2. Inheritance Errors
```typescript
{
  "code": "INHERITANCE_ERROR", 
  "message": "Inheritance constraint violation",
  "details": {
    "parent_string_id": number,
    "child_string_id": number,
    "conflicting_field": string,
    "parent_value": string,
    "child_value": string
  }
}
```

### 3. Concurrency Errors
```typescript
{
  "code": "CONCURRENT_MODIFICATION",
  "message": "String was modified by another user",
  "details": {
    "string_id": number,
    "last_modified": string,
    "modified_by": string,
    "current_version": number,
    "requested_version": number
  }
}
```

## Testing Requirements

### 1. Unit Tests
- Inheritance calculation algorithms
- Validation logic for each field type
- Conflict detection and resolution
- Rollback functionality

### 2. Integration Tests
- Full update workflows with inheritance
- Concurrent modification scenarios
- Large batch update performance
- Error recovery and rollback

### 3. Performance Tests
- Batch updates with 1000+ strings
- Deep inheritance chains (5+ levels)
- Concurrent user scenarios
- Database query optimization validation

## Security Considerations

### 1. Authorization
- Verify user has update permissions for workspace/rule/field
- Audit all string modifications with user attribution
- Prevent unauthorized access to string history

### 2. Data Integrity
- Validate all input data to prevent injection attacks
- Ensure atomic operations to prevent data corruption
- Backup critical data before major operations

### 3. Rate Limiting
- Implement rate limiting for batch operations
- Prevent abuse of inheritance analysis endpoint
- Monitor for unusual update patterns

## Migration Plan

### 1. Database Migration
```sql
-- Create new tables
-- Add indexes
-- Migrate existing string data to new schema
-- Update existing inheritance relationships
```

### 2. API Versioning
- Maintain backward compatibility with existing string APIs
- Gradual migration to new update endpoints
- Feature flags for new functionality

### 3. Rollout Strategy
1. Deploy database schema changes
2. Deploy new API endpoints (disabled)
3. Enable endpoints with feature flags
4. Migrate frontend to use new endpoints
5. Deprecate old update mechanisms

## Frontend Integration Points

The frontend expects the following integration:

1. **String Selection**: Existing `/api/workspaces/{workspaceId}/strings/by-field/{fieldId}` endpoint (already implemented)

2. **Update Workflow**: New batch update endpoint for processing grid changes

3. **Impact Preview**: New impact analysis endpoint for showing inheritance effects

4. **Validation**: Real-time validation through the batch update endpoint with `dry_run: true`

5. **History/Rollback**: New endpoints for tracking and reverting changes

### Case Conversion Note

**Important**: The backend uses `snake_case` while the frontend uses `camelCase`. The existing `apiFetch()` utility in `src/lib/api-utils.ts` automatically handles case conversion:

- **Frontend → Backend**: `camelCase` properties are converted to `snake_case`
- **Backend → Frontend**: `snake_case` properties are converted to `camelCase`

This means:
- Frontend will send: `{ stringId: 123, fieldUpdates: {...} }`
- Backend will receive: `{ string_id: 123, field_updates: {...} }`
- Backend will respond: `{ updated_strings: [...], affected_strings: [...] }`
- Frontend will receive: `{ updatedStrings: [...], affectedStrings: [...] }`

**All API specifications in this document use snake_case as that's what the backend will actually implement.**

## Success Criteria

- [ ] All string updates preserve inheritance relationships correctly
- [ ] Batch operations are atomic (all succeed or all fail)
- [ ] Impact analysis accurately predicts inheritance effects
- [ ] Performance acceptable for batches up to 1000 strings
- [ ] Comprehensive audit trail for all modifications
- [ ] Rollback functionality works for all update types
- [ ] No data corruption or orphaned strings
- [ ] Concurrent user operations handle conflicts gracefully

## Questions for Backend Team

1. **Database Choice**: Are there any constraints on the JSONB usage for field storage?
2. **Async Processing**: Should large inheritance updates be processed asynchronously?
3. **Caching Strategy**: What caching mechanisms are available for inheritance relationships?
4. **Monitoring**: What metrics should be tracked for update operations?
5. **Backup Strategy**: How should we handle backup creation and retention?
6. **Performance SLA**: What are the acceptable response times for batch operations?

---

# Original Phase 4 Tasks

## Tasks

### Task 4.1: Bulk Update API Design
**Backend Files**: New API endpoints needed
**Estimated Time**: 12 hours

**Requirements**:
- Design REST API endpoints for bulk string updates
- Support inheritance propagation in backend
- Implement atomic transaction handling
- Add conflict detection and resolution

**API Endpoints Needed**:

```typescript
// New endpoints to be implemented in backend
POST /api/v1/strings/bulk-update/
POST /api/v1/strings/preview-inheritance-impact/
PUT /api/v1/nested-submissions/{id}/
PATCH /api/v1/strings/{id}/with-inheritance/
POST /api/v1/strings/validate-update-batch/
```

**Request/Response Interfaces**:
```typescript
interface BulkUpdateRequest {
  updates: Array<{
    stringId: number;
    stringUuid: string;
    newValue: string;
    blockItems: BlockItem[];
    maintainInheritance: boolean;
    conflictResolution: 'abort' | 'overwrite' | 'merge';
  }>;
  options: {
    propagateToChildren: boolean;
    validateBeforeUpdate: boolean;
    createBackup: boolean;
    batchSize: number;
  };
  metadata: {
    updatedBy: number;
    updateReason: string;
    clientVersion: string;
  };
}

interface BulkUpdateResponse {
  success: boolean;
  processedCount: number;
  failedCount: number;
  results: Array<{
    stringId: number;
    status: 'success' | 'failed' | 'skipped';
    newValue?: string;
    error?: string;
    affectedChildren?: number[];
  }>;
  backupId?: string;
  processingTime: number;
  warnings: string[];
}

interface InheritanceImpactRequest {
  parentStringIds: number[];
  proposedChanges: Array<{
    stringId: number;
    newValue: string;
    newBlockItems: BlockItem[];
  }>;
  options: {
    includePreview: boolean;
    maxDepth: number;
    includeMetadata: boolean;
  };
}

interface InheritanceImpactResponse {
  totalAffectedStrings: number;
  affectedByLevel: { [level: number]: number };
  impactTree: InheritanceImpactNode[];
  estimatedProcessingTime: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  conflicts: ConflictInfo[];
  warnings: string[];
}
```

**Backend Requirements Documentation**:
- Database schema changes needed for tracking updates
- Transaction handling for atomic bulk operations
- Inheritance calculation algorithms
- Conflict detection mechanisms
- Performance optimization strategies
- Backup and rollback procedures

**Acceptance Criteria**:
- [ ] API design supports all required update operations
- [ ] Inheritance propagation is handled correctly
- [ ] Atomic transactions prevent partial failures
- [ ] Conflict detection works reliably
- [ ] API performance meets requirements (<5 seconds for 100 strings)

### Task 4.2: Frontend API Integration Layer
**File**: `src/lib/api/stringUpdates.ts`
**Estimated Time**: 8 hours

**Requirements**:
- Create API client functions for update operations
- Implement error handling and retry logic
- Add progress tracking for long operations
- Support cancellation of in-progress updates

**Implementation Details**:
- Create typed API client functions
- Implement exponential backoff for retries
- Add request/response interceptors for common operations
- Support request cancellation via AbortController
- Add comprehensive error mapping

**API Client Functions**:
```typescript
// src/lib/api/stringUpdates.ts
export interface StringUpdateClient {
  bulkUpdateStrings: (request: BulkUpdateRequest) => Promise<BulkUpdateResponse>;
  previewInheritanceImpact: (request: InheritanceImpactRequest) => Promise<InheritanceImpactResponse>;
  validateUpdateBatch: (strings: UpdateValidation[]) => Promise<ValidationResult[]>;
  updateNestedSubmissionWithStrings: (id: number, data: NestedSubmissionUpdate) => Promise<SubmissionNestedResponse>;
  cancelUpdateOperation: (operationId: string) => Promise<void>;
  getUpdateStatus: (operationId: string) => Promise<UpdateStatus>;
}

// Progress tracking for long operations
export interface UpdateProgress {
  operationId: string;
  totalItems: number;
  processedItems: number;
  failedItems: number;
  currentPhase: 'validating' | 'updating' | 'propagating' | 'finalizing';
  estimatedTimeRemaining: number;
  errors: UpdateError[];
}

// Error handling
export interface UpdateError {
  stringId: number;
  error: string;
  errorCode: string;
  isRetryable: boolean;
  suggestedAction: string;
}
```

**Error Handling Strategy**:
- Network errors: Automatic retry with exponential backoff
- Validation errors: Surface to user immediately
- Conflict errors: Trigger conflict resolution workflow
- Timeout errors: Allow user to continue or cancel
- Server errors: Log for debugging, show user-friendly message

**Acceptance Criteria**:
- [ ] All API endpoints have corresponding client functions
- [ ] Error handling is comprehensive and user-friendly
- [ ] Progress tracking works for long operations
- [ ] Request cancellation works correctly
- [ ] Retry logic handles temporary failures gracefully

### Task 4.3: Update Operation Orchestrator
**File**: `src/utils/grid-builder/updateOrchestrator.ts`
**Estimated Time**: 10 hours

**Requirements**:
- Orchestrate complex multi-step update operations
- Handle partial failures and recovery
- Provide real-time progress updates
- Support rollback on critical failures

**Implementation Details**:
- Create state machine for update workflow
- Implement operation queuing and batching
- Add checkpoint and rollback capabilities
- Provide granular progress reporting
- Handle complex dependency resolution

**Orchestrator Functions**:
```typescript
interface UpdateOrchestrator {
  planUpdateOperation: (changes: GridChange[]) => Promise<UpdatePlan>;
  executeUpdatePlan: (plan: UpdatePlan, options: ExecutionOptions) => Promise<UpdateResult>;
  monitorProgress: (operationId: string, callback: ProgressCallback) => void;
  pauseOperation: (operationId: string) => Promise<void>;
  resumeOperation: (operationId: string) => Promise<void>;
  rollbackOperation: (operationId: string) => Promise<RollbackResult>;
}

interface UpdatePlan {
  operationId: string;
  phases: UpdatePhase[];
  totalSteps: number;
  estimatedDuration: number;
  dependencies: DependencyMap;
  rollbackStrategy: RollbackStrategy;
  riskAssessment: RiskAssessment;
}

interface UpdatePhase {
  name: string;
  description: string;
  steps: UpdateStep[];
  dependencies: string[];
  isParallel: boolean;
  timeoutMs: number;
}

interface UpdateStep {
  id: string;
  type: 'validate' | 'update' | 'propagate' | 'verify';
  stringIds: number[];
  operation: UpdateOperation;
  retryCount: number;
  isRollbackable: boolean;
}
```

**Workflow States**:
1. **Planning**: Analyze changes and create execution plan
2. **Validation**: Validate all changes before execution
3. **Backup**: Create rollback point if needed
4. **Execution**: Execute updates in planned order
5. **Propagation**: Apply inheritance changes
6. **Verification**: Verify results and check consistency
7. **Completion**: Finalize operation and cleanup

**Acceptance Criteria**:
- [ ] Orchestrator handles complex multi-step operations
- [ ] Partial failures are handled gracefully
- [ ] Progress reporting is accurate and real-time
- [ ] Rollback capability works correctly
- [ ] Operation can be paused and resumed

### Task 4.4: Conflict Detection and Resolution
**File**: `src/utils/grid-builder/conflictResolution.ts`
**Estimated Time**: 8 hours

**Requirements**:
- Detect conflicts between user changes and current database state
- Provide conflict resolution strategies
- Support manual conflict resolution by users
- Implement optimistic locking mechanisms

**Implementation Details**:
- Compare user changes with current database state
- Identify different types of conflicts (value, structure, timing)
- Provide automatic resolution strategies where possible
- Create UI for manual conflict resolution
- Implement versioning and locking mechanisms

**Conflict Types and Resolution**:
```typescript
interface ConflictDetector {
  detectConflicts: (changes: ProposedChange[]) => Promise<ConflictInfo[]>;
  suggestResolutions: (conflicts: ConflictInfo[]) => ResolutionSuggestion[];
  applyResolution: (conflict: ConflictInfo, resolution: Resolution) => Promise<ResolvedChange>;
  validateResolution: (resolution: Resolution) => ValidationResult;
}

interface ConflictInfo {
  stringId: number;
  conflictType: 'value' | 'structure' | 'timing' | 'dependency';
  severity: 'low' | 'medium' | 'high' | 'blocking';
  userValue: any;
  currentValue: any;
  lastModified: Date;
  lastModifiedBy: number;
  description: string;
  affectedChildren: number[];
}

interface ResolutionStrategy {
  type: 'take_theirs' | 'take_mine' | 'merge' | 'skip' | 'manual';
  description: string;
  isAutomatic: boolean;
  riskLevel: 'low' | 'medium' | 'high';
  preview: string;
}

enum ConflictResolutionMode {
  ABORT_ON_CONFLICT = 'abort',           // Stop on first conflict
  SKIP_CONFLICTS = 'skip',               // Skip conflicting items
  AUTO_RESOLVE = 'auto',                 // Automatically resolve where possible
  MANUAL_RESOLVE = 'manual'              // Require user input for all conflicts
}
```

**Conflict Resolution UI**:
- Side-by-side comparison of conflicting values
- Three-way merge interface for complex conflicts
- Batch resolution for similar conflicts
- Preview of resolution effects
- Ability to defer conflict resolution

**Acceptance Criteria**:
- [ ] All conflict types are detected accurately
- [ ] Automatic resolution works for simple conflicts
- [ ] Manual resolution interface is intuitive
- [ ] Conflict resolution doesn't break inheritance chains
- [ ] Performance is acceptable with many conflicts

### Task 4.5: Integration Testing Framework
**File**: `src/utils/testing/updateOperationTesting.ts`
**Estimated Time**: 6 hours

**Requirements**:
- Create comprehensive testing framework for update operations
- Support mocking of complex backend scenarios
- Test error conditions and edge cases
- Performance testing for large datasets

**Implementation Details**:
- Create mock API responses for different scenarios
- Test data generators for complex inheritance hierarchies
- Automated testing of error conditions
- Performance benchmarking utilities
- Integration test helpers

**Testing Utilities**:
```typescript
interface UpdateTestingFramework {
  createTestHierarchy: (config: HierarchyConfig) => TestStringHierarchy;
  mockAPIResponses: (scenario: TestScenario) => MockConfiguration;
  simulateConflicts: (conflictTypes: ConflictType[]) => ConflictSimulation;
  benchmarkPerformance: (operation: UpdateOperation) => PerformanceBenchmark;
  validateIntegrity: (beforeState: any, afterState: any) => IntegrityReport;
}

interface TestScenario {
  name: string;
  description: string;
  stringCount: number;
  hierarchyDepth: number;
  conflictRate: number;
  errorRate: number;
  networkLatency: number;
}

interface HierarchyConfig {
  levels: number;
  branchingFactor: number;
  inheritancePatterns: InheritancePattern[];
  dataTypes: FieldType[];
  conflictProbability: number;
}
```

**Test Scenarios**:
- Large hierarchy updates (1000+ strings)
- High conflict rate scenarios
- Network failure and recovery
- Partial failure and rollback
- Concurrent update conflicts
- Performance under load

**Acceptance Criteria**:
- [ ] Testing framework covers all update scenarios
- [ ] Mock responses accurately simulate backend behavior  
- [ ] Performance benchmarks identify bottlenecks
- [ ] Integration tests catch regression issues
- [ ] Error condition testing is comprehensive

## Testing Requirements

### Unit Tests
- [ ] API client functions with various response scenarios
- [ ] Update orchestrator state machine logic
- [ ] Conflict detection algorithms
- [ ] Error handling and retry mechanisms
- [ ] Progress tracking and reporting

### Integration Tests
- [ ] End-to-end update workflows
- [ ] Backend API integration
- [ ] Conflict resolution workflows
- [ ] Error recovery mechanisms
- [ ] Performance with realistic datasets

### Performance Tests
- [ ] Bulk update operations complete within 5 seconds for 100 strings
- [ ] Inheritance impact calculation within 3 seconds for 500 affected strings
- [ ] Conflict detection completes within 2 seconds for 50 conflicts
- [ ] Memory usage remains stable during large operations

### E2E Tests
- [ ] Complete update workflow from string selection to completion
- [ ] Conflict resolution with manual intervention
- [ ] Error handling with retry and recovery
- [ ] Operation cancellation and rollback
- [ ] Progress tracking and user feedback

## Dependencies
- Phase 3 completion (inheritance analysis)
- Backend API implementation
- Enhanced database schema for update tracking
- Performance monitoring and alerting

## Definition of Done
- [ ] All tasks completed and tested
- [ ] Backend API integration working correctly
- [ ] Comprehensive error handling implemented
- [ ] Performance requirements met
- [ ] Conflict resolution working reliably
- [ ] Update operations are atomic and reliable
- [ ] Progress tracking provides accurate feedback
- [ ] System can handle complex inheritance scenarios
- [ ] Rollback capability tested and verified