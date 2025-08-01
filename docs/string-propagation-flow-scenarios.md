# String Detail Update Propagation Flow Scenarios

## Overview

This document provides detailed pseudo flow examples of what happens when a user updates a string detail, including both the current implementation and the proposed enhanced flow.

## Scenario Setup

### Test Hierarchy
```
Level 1: "Nike-Summer2024" (Parent)
├── Level 2: "Nike-Summer2024-US" (Child 1)
│   └── Level 3: "Nike-Summer2024-US-Digital" (Grandchild 1)
└── Level 2: "Nike-Summer2024-EU" (Child 2)
    └── Level 3: "Nike-Summer2024-EU-Print" (Grandchild 2)

User Action: Update Brand dimension from "Nike" → "Adidas" on Level 1 string
```

## Current Flow (Existing Implementation)

```
1. USER ACTION
   ├── User calls: PUT /string-details/123/
   ├── Payload: {"dimension_value": 456}  // Adidas dimension value
   └── Endpoint: StringDetailViewSet.update()

2. STRINGDETAIL UPDATE
   ├── StringDetail.save() called
   ├── Database update: dimension_value = 456
   └── Django signals triggered

3. SIGNAL HANDLER TRIGGERED
   ├── Signal: post_save(sender=StringDetail)
   ├── Handler: auto_regenerate_string_on_detail_update()
   ├── Check: created=False (it's an update, not creation)
   └── Check: AUTO_REGENERATE_STRINGS=True

4. PARENT STRING REGENERATION
   ├── Get parent string: "Nike-Summer2024"
   ├── Get all dimension values: {"Brand": "Adidas", "Campaign": "Summer2024"}
   ├── Call: StringGenerationService.generate_string_value()
   ├── New value generated: "Adidas-Summer2024"
   ├── String.value updated
   ├── String.version incremented
   └── generation_metadata updated

5. INHERITANCE PROPAGATION (if ENABLE_INHERITANCE_PROPAGATION=True)
   ├── Call: _propagate_to_child_strings(parent_string)
   ├── Get children: ["Nike-Summer2024-US", "Nike-Summer2024-EU"]
   ├── For each child:
   │   ├── Get child's dimension values
   │   ├── Call: child.regenerate_value()
   │   ├── New values: ["Adidas-Summer2024-US", "Adidas-Summer2024-EU"]
   │   └── Recursive call for grandchildren
   └── Final hierarchy:
       ├── "Adidas-Summer2024"
       ├── "Adidas-Summer2024-US"
       ├── "Adidas-Summer2024-US-Digital"
       ├── "Adidas-Summer2024-EU"
       └── "Adidas-Summer2024-EU-Print"

6. RESPONSE
   └── Return: Updated StringDetail with 200 OK
```

## Enhanced Flow (Proposed Implementation)

```
1. USER ACTION
   ├── User calls: PUT /string-details/123/
   ├── Payload: {
   │   "dimension_value": 456,
   │   "propagate": true,
   │   "dry_run": false
   │   }
   └── Endpoint: StringDetailViewSet.update()

2. PRE-UPDATE ANALYSIS (New)
   ├── Call: PropagationService.analyze_impact()
   ├── Detect hierarchy: 5 strings affected
   ├── Generate preview:
   │   ├── "Nike-Summer2024" → "Adidas-Summer2024"
   │   ├── "Nike-Summer2024-US" → "Adidas-Summer2024-US"
   │   ├── etc...
   ├── Check for conflicts: None found
   └── Estimate processing time: 0.5 seconds

3. STRINGDETAIL UPDATE (Enhanced)
   ├── Start database transaction
   ├── Capture old values for rollback
   ├── StringDetail.save() with change tracking
   ├── Log change in PropagationJob table
   └── Django signals triggered

4. ENHANCED SIGNAL HANDLER
   ├── Signal: post_save(sender=StringDetail)
   ├── Handler: enhanced_auto_regenerate_handler()
   ├── Detect changed fields: {"dimension_value": {"old": 123, "new": 456}}
   ├── Check propagation settings
   └── Queue propagation job if needed

5. PROPAGATION SERVICE EXECUTION
   ├── Start: PropagationJob(status='running')
   ├── Get hierarchy with optimized queries
   ├── Process in order (breadth-first):
   │   ├── Level 1: "Nike-Summer2024"
   │   │   ├── Update to "Adidas-Summer2024"
   │   │   ├── Create StringModification record
   │   │   └── Mark as processed
   │   ├── Level 2: Children in parallel
   │   │   ├── "Nike-Summer2024-US" → "Adidas-Summer2024-US"
   │   │   └── "Nike-Summer2024-EU" → "Adidas-Summer2024-EU"
   │   └── Level 3: Grandchildren
   │       ├── "Nike-Summer2024-US-Digital" → "Adidas-Summer2024-US-Digital"
   │       └── "Nike-Summer2024-EU-Print" → "Adidas-Summer2024-EU-Print"
   └── Update job status to 'completed'

6. AUDIT TRAIL CREATION
   ├── StringModification records for each change
   ├── StringInheritanceUpdate linking parent→child changes
   ├── PropagationJob summary record
   └── Version increments on all affected strings

7. ERROR HANDLING (if needed)
   ├── If error on Level 2: Continue with other children
   ├── If critical error: Rollback transaction
   ├── Log errors in PropagationError table
   └── Send notification to user

8. RESPONSE ENHANCEMENT
   ├── Return: Updated StringDetail
   ├── Include: {
   │   "propagation_summary": {
   │     "total_affected": 5,
   │     "successful": 5,
   │     "failed": 0,
   │     "job_id": "uuid-123"
   │   }
   │   }
   └── Status: 200 OK

9. BACKGROUND PROCESSING (for large hierarchies)
   ├── If hierarchy > 100 strings:
   │   ├── Queue Celery task
   │   ├── Return immediate response with job_id
   │   ├── User can poll: GET /propagation-jobs/uuid-123/
   │   └── WebSocket updates for real-time progress
   └── Process asynchronously with progress tracking
```

## Error Scenarios

### Scenario 1: Child String Update Fails

```
SCENARIO: Child String Update Fails
├── Level 1 updated successfully: "Adidas-Summer2024" ✓
├── Level 2 Child 1 fails: Database error ✗
├── Level 2 Child 2 continues: "Adidas-Summer2024-EU" ✓
├── Level 3 under Child 2: "Adidas-Summer2024-EU-Print" ✓
├── Error logged with context
├── User notified of partial success
└── Retry mechanism available

Flow Details:
1. StringDetail update succeeds
2. Parent string "Nike-Summer2024" → "Adidas-Summer2024" ✓
3. Child 1 processing starts
4. Database constraint violation on Child 1 ✗
5. Error captured: 
   {
     "string_id": 456,
     "error": "Duplicate string value",
     "original_value": "Nike-Summer2024-US",
     "attempted_value": "Adidas-Summer2024-US"
   }
6. Child 2 processing continues independently
7. Child 2 update succeeds: "Adidas-Summer2024-EU" ✓
8. Grandchild 2 inherits: "Adidas-Summer2024-EU-Print" ✓
9. Final state:
   ├── "Adidas-Summer2024" ✓ (Parent updated)
   ├── "Nike-Summer2024-US" ✗ (Child 1 failed - old value retained)
   ├── "Nike-Summer2024-US-Digital" ✗ (Grandchild 1 skipped due to parent failure)
   ├── "Adidas-Summer2024-EU" ✓ (Child 2 updated)
   └── "Adidas-Summer2024-EU-Print" ✓ (Grandchild 2 updated)
10. Response:
    {
      "propagation_summary": {
        "total_affected": 5,
        "successful": 3,
        "failed": 2,
        "errors": [
          {
            "string_id": 456,
            "error": "Duplicate string value",
            "retry_available": true
          }
        ]
      }
    }
```

### Scenario 2: Circular Dependency Detected

```
SCENARIO: Circular Dependency Detected
├── Before update: Check for cycles
├── Detection: Child 1 → Parent relationship would create loop
├── Block update with clear error message
├── Suggest hierarchy restructuring
└── No changes committed

Flow Details:
1. User attempts: PUT /string-details/123/
2. Pre-update validation triggered
3. Circular dependency check:
   Current: A → B → C
   Proposed: A → B → C → A (CYCLE DETECTED)
4. Validation fails:
   {
     "error": "Circular dependency detected",
     "cycle_path": ["String A", "String B", "String C", "String A"],
     "suggested_actions": [
       "Remove parent relationship from String C",
       "Create new hierarchy branch"
     ]
   }
5. HTTP 400 Bad Request returned
6. No database changes committed
7. User receives actionable error message
```

### Scenario 3: Large Hierarchy Processing

```
SCENARIO: Large Hierarchy (1000+ strings)
├── Impact analysis shows large scope
├── Queue background job immediately
├── Return job_id to user
├── Process in chunks of 100
├── Send progress notifications
└── Complete with summary report

Flow Details:
1. User calls: PUT /string-details/123/
2. Impact analysis detects 1,247 affected strings
3. System decides: BACKGROUND_PROCESSING_THRESHOLD exceeded
4. Immediate response returned:
   {
     "status": "queued",
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "estimated_completion": "2024-01-15T14:35:00Z",
     "affected_strings_count": 1247,
     "tracking_url": "/api/propagation-jobs/550e8400-e29b-41d4-a716-446655440000/"
   }
5. Background processing begins:
   ├── Chunk 1: Strings 1-100 (Level 1-2)
   ├── Chunk 2: Strings 101-200 (Level 2-3)
   ├── ... (continue in breadth-first order)
   └── Chunk 13: Strings 1201-1247 (Final level)
6. Progress updates via WebSocket:
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "processing",
     "progress": {
       "processed": 450,
       "total": 1247,
       "percentage": 36,
       "current_level": 3,
       "estimated_remaining": "00:04:23"
     }
   }
7. Completion notification:
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "status": "completed",
     "summary": {
       "total_affected": 1247,
       "successful": 1244,
       "failed": 3,
       "duration": "00:06:42",
       "errors": [...]
     }
   }
```

### Scenario 4: Dry Run Preview

```
SCENARIO: User Requests Preview Before Update
├── dry_run: true parameter sent
├── Full impact analysis performed
├── No actual changes committed
├── Preview results returned
└── User can then confirm or cancel

Flow Details:
1. User calls: PUT /string-details/123/
   {
     "dimension_value": 456,
     "dry_run": true
   }
2. System performs full analysis without commits
3. Preview response:
   {
     "dry_run": true,
     "preview": {
       "changes": [
         {
           "string_id": 789,
           "current_value": "Nike-Summer2024",
           "new_value": "Adidas-Summer2024",
           "level": 1,
           "change_type": "direct"
         },
         {
           "string_id": 790,
           "current_value": "Nike-Summer2024-US",
           "new_value": "Adidas-Summer2024-US", 
           "level": 2,
           "change_type": "inherited"
         }
       ],
       "summary": {
         "total_affected": 5,
         "by_level": {
           "1": 1,
           "2": 2, 
           "3": 2
         },
         "estimated_duration": "0.5s"
       },
       "warnings": [],
       "conflicts": []
     }
   }
4. User can then make actual update:
   PUT /string-details/123/
   {
     "dimension_value": 456,
     "dry_run": false,
     "confirm_preview": true
   }
```

### Scenario 5: Rollback Operation

```
SCENARIO: User Requests Rollback After Failed Update
├── Identify batch operation to rollback
├── Reverse all changes in order
├── Restore original values
├── Update audit trail
└── Confirm rollback completion

Flow Details:
1. Original update partially failed (3 of 5 strings updated)
2. User requests rollback:
   POST /strings/rollback/
   {
     "job_id": "550e8400-e29b-41d4-a716-446655440000",
     "rollback_type": "full"
   }
3. System identifies changes to reverse:
   ├── "Adidas-Summer2024" → "Nike-Summer2024"
   ├── "Adidas-Summer2024-EU" → "Nike-Summer2024-EU"  
   └── "Adidas-Summer2024-EU-Print" → "Nike-Summer2024-EU-Print"
4. Rollback processing:
   ├── Start new PropagationJob (type: rollback)
   ├── Process in reverse dependency order
   ├── Update StringModification records
   ├── Increment version numbers
   └── Mark original job as rolled back
5. Rollback confirmation:
   {
     "rollback_job_id": "661f9511-f3ac-52e5-b827-557766551111",
     "status": "completed",
     "reverted_changes": 3,
     "final_state": "All changes successfully rolled back"
   }
```

## Configuration Impact on Flows

### Conservative Configuration
```python
MASTER_DATA_CONFIG = {
    'AUTO_REGENERATE_STRINGS': True,
    'ENABLE_INHERITANCE_PROPAGATION': False,  # Disabled
    'PROPAGATION_MODE': 'manual',
    'MAX_INHERITANCE_DEPTH': 3
}

Result: Only direct string updates, no child propagation
```

### Aggressive Configuration  
```python
MASTER_DATA_CONFIG = {
    'AUTO_REGENERATE_STRINGS': True,
    'ENABLE_INHERITANCE_PROPAGATION': True,
    'PROPAGATION_MODE': 'automatic',
    'MAX_INHERITANCE_DEPTH': 50,
    'PARALLEL_PROPAGATION': True,
    'BACKGROUND_PROCESSING_THRESHOLD': 10
}

Result: Full hierarchy updates with background processing for small hierarchies
```

### Selective Configuration
```python
MASTER_DATA_CONFIG = {
    'FIELD_PROPAGATION_RULES': {
        'dimension_value': 'inherit_always',
        'dimension_value_freetext': 'inherit_if_empty', 
        'custom_metadata': 'inherit_never'
    }
}

Result: Field-specific inheritance behavior
```

## Performance Characteristics

### Small Hierarchy (< 10 strings)
- **Processing Time**: < 1 second
- **Method**: Synchronous processing
- **Response**: Complete results immediately

### Medium Hierarchy (10-100 strings)  
- **Processing Time**: 1-10 seconds
- **Method**: Synchronous with progress tracking
- **Response**: Complete results with timing info

### Large Hierarchy (100+ strings)
- **Processing Time**: 10+ seconds  
- **Method**: Background processing
- **Response**: Job ID with polling endpoint

## Monitoring and Observability

### Metrics Tracked
- Propagation job completion rates
- Average processing time by hierarchy size
- Error rates by error type
- User satisfaction with preview accuracy

### Logging Examples
```
INFO: Propagation job started: job_id=123, affected_strings=45
INFO: Level 1 processing complete: 1/1 successful
WARN: Level 2 partial failure: 3/4 successful, 1 failed
ERROR: String update failed: string_id=456, error=constraint_violation
INFO: Propagation job completed: job_id=123, duration=2.3s, success_rate=95%
```

This comprehensive flow documentation provides clear guidance for both implementation and troubleshooting of the string propagation system.