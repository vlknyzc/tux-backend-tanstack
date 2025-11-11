# Propagation API

Propagation manages automatic updates to child strings when parent strings or dimension values change. It ensures naming consistency across hierarchies.

**Base Path**: `/api/v1/workspaces/{workspace_id}/propagation-*`

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/propagation-jobs/` | List propagation jobs |
| GET | `/propagation-jobs/{id}/` | Get job details |
| POST | `/propagation-jobs/{id}/retry/` | Retry failed job |
| GET | `/propagation-errors/` | List propagation errors |
| GET | `/propagation-settings/` | Get workspace propagation settings |
| PATCH | `/propagation-settings/` | Update settings |

---

## Data Models

### Propagation Job Object

```json
{
  "id": 150,
  "workspace": 1,
  "job_type": "dimension_value_change",
  "status": "completed",
  "triggered_by": {
    "id": 5,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "source_string": {
    "id": 501,
    "value": "ACME-2024-US-Q4-Awareness",
    "string_uuid": "abc123-def456"
  },
  "affected_strings_count": 15,
  "processed_count": 15,
  "failed_count": 0,
  "metadata": {
    "dimension_id": 1,
    "old_value": "US",
    "new_value": "EU",
    "change_reason": "Region update requested by marketing team"
  },
  "started_at": "2024-11-11T10:00:00Z",
  "completed_at": "2024-11-11T10:00:15Z",
  "processing_time_seconds": 15,
  "created": "2024-11-11T10:00:00Z"
}
```

### Propagation Error Object

```json
{
  "id": 75,
  "job": {
    "id": 150,
    "job_type": "dimension_value_change"
  },
  "string": {
    "id": 505,
    "value": "ACME-2024-US-Q4-Awareness-Premium",
    "string_uuid": "xyz789-abc123"
  },
  "error_type": "validation_error",
  "error_message": "New dimension value conflicts with entity constraints",
  "error_details": {
    "dimension": "region",
    "attempted_value": "EU",
    "constraint": "Region EU not allowed for Premium tier"
  },
  "is_resolved": false,
  "resolved_at": null,
  "resolved_by": null,
  "created": "2024-11-11T10:00:10Z"
}
```

### Propagation Settings Object

```json
{
  "workspace": 1,
  "auto_propagate": true,
  "require_approval": false,
  "notify_on_completion": true,
  "notify_on_errors": true,
  "batch_size": 100,
  "retry_attempts": 3,
  "retry_delay_seconds": 60
}
```

---

## Job Status Types

| Status | Description |
|--------|-------------|
| `pending` | Job queued but not started |
| `running` | Job currently processing |
| `completed` | Job finished successfully |
| `partial` | Job completed with some errors |
| `failed` | Job failed completely |
| `cancelled` | Job was cancelled |

## Job Types

| Type | Trigger | Description |
|------|---------|-------------|
| `dimension_value_change` | Dimension value updated | Updates all strings using that value |
| `parent_string_change` | Parent string modified | Updates all child strings |
| `rule_pattern_change` | Rule pattern modified | Regenerates all strings using that rule |
| `manual_propagation` | User-initiated | Manual propagation request |

---

## List Propagation Jobs

**GET** `/api/v1/workspaces/{workspace_id}/propagation-jobs/`

Get all propagation jobs for a workspace.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `job_type` | string | Filter by job type |
| `source_string_id` | integer | Filter by source string |
| `triggered_by` | integer | Filter by user who triggered |
| `date_from` | date | Filter jobs after this date |
| `date_to` | date | Filter jobs before this date |
| `page` | integer | Page number |
| `page_size` | integer | Results per page |

### Example Request

```bash
GET /api/v1/workspaces/1/propagation-jobs/?status=completed&page_size=20
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
{
  "count": 150,
  "next": "http://api.../propagation-jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 150,
      "job_type": "dimension_value_change",
      "status": "completed",
      "triggered_by": {...},
      "source_string": {...},
      "affected_strings_count": 15,
      "processed_count": 15,
      "failed_count": 0,
      "started_at": "2024-11-11T10:00:00Z",
      "completed_at": "2024-11-11T10:00:15Z",
      "processing_time_seconds": 15
    },
    {
      "id": 149,
      "job_type": "parent_string_change",
      "status": "partial",
      "triggered_by": {...},
      "source_string": {...},
      "affected_strings_count": 8,
      "processed_count": 7,
      "failed_count": 1,
      "started_at": "2024-11-11T09:30:00Z",
      "completed_at": "2024-11-11T09:30:05Z",
      "processing_time_seconds": 5
    }
  ]
}
```

---

## Get Job Details

**GET** `/api/v1/workspaces/{workspace_id}/propagation-jobs/{id}/`

Get detailed information about a propagation job.

### Example Response (200 OK)

```json
{
  "id": 150,
  "workspace": 1,
  "job_type": "dimension_value_change",
  "status": "completed",
  "triggered_by": {
    "id": 5,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "source_string": {
    "id": 501,
    "value": "ACME-2024-US-Q4-Awareness",
    "string_uuid": "abc123-def456",
    "project": {
      "id": 10,
      "name": "Q4 2024 Campaign"
    }
  },
  "affected_strings": [
    {
      "id": 502,
      "value": "ACME-2024-US-Q4-Awareness-Premium",
      "status": "updated"
    },
    {
      "id": 503,
      "value": "ACME-2024-US-Q4-Awareness-Standard",
      "status": "updated"
    }
  ],
  "affected_strings_count": 15,
  "processed_count": 15,
  "failed_count": 0,
  "errors": [],
  "metadata": {
    "dimension_id": 1,
    "dimension_name": "region",
    "old_value": "US",
    "new_value": "EU",
    "change_reason": "Market expansion to Europe"
  },
  "started_at": "2024-11-11T10:00:00Z",
  "completed_at": "2024-11-11T10:00:15Z",
  "processing_time_seconds": 15,
  "created": "2024-11-11T10:00:00Z"
}
```

---

## Retry Failed Job

**POST** `/api/v1/workspaces/{workspace_id}/propagation-jobs/{id}/retry/`

Retry a failed or partial propagation job.

### Request Body (Optional)

```json
{
  "retry_failed_only": true,
  "reason": "Fixed constraint issue"
}
```

### Example Response (200 OK)

```json
{
  "success": true,
  "new_job_id": 151,
  "message": "Propagation job queued for retry",
  "affected_strings_count": 5
}
```

---

## List Propagation Errors

**GET** `/api/v1/workspaces/{workspace_id}/propagation-errors/`

Get all propagation errors for a workspace.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | integer | Filter by job |
| `is_resolved` | boolean | Filter resolved/unresolved |
| `error_type` | string | Filter by error type |
| `string_id` | integer | Filter by string |

### Example Request

```bash
GET /api/v1/workspaces/1/propagation-errors/?is_resolved=false
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 75,
      "job": {
        "id": 149,
        "job_type": "parent_string_change",
        "status": "partial"
      },
      "string": {
        "id": 505,
        "value": "ACME-2024-US-Q4-Awareness-Premium",
        "project": {
          "id": 10,
          "name": "Q4 2024 Campaign"
        }
      },
      "error_type": "validation_error",
      "error_message": "Dimension value conflicts with entity constraints",
      "error_details": {...},
      "is_resolved": false,
      "created": "2024-11-11T09:30:05Z"
    }
  ]
}
```

---

## Get Propagation Settings

**GET** `/api/v1/workspaces/{workspace_id}/propagation-settings/`

Get propagation configuration for a workspace.

### Example Response (200 OK)

```json
{
  "workspace": 1,
  "auto_propagate": true,
  "require_approval": false,
  "notify_on_completion": true,
  "notify_on_errors": true,
  "batch_size": 100,
  "retry_attempts": 3,
  "retry_delay_seconds": 60,
  "allowed_job_types": [
    "dimension_value_change",
    "parent_string_change",
    "rule_pattern_change",
    "manual_propagation"
  ]
}
```

---

## Update Propagation Settings

**PATCH** `/api/v1/workspaces/{workspace_id}/propagation-settings/`

Update workspace propagation settings.

### Request Body (Partial Update)

```json
{
  "auto_propagate": false,
  "require_approval": true,
  "batch_size": 50
}
```

### Example Response (200 OK)

Returns updated settings object.

---

## Frontend Integration Examples

### Fetch Propagation Jobs

```javascript
async function fetchPropagationJobs(workspaceId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/propagation-jobs/?${params}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  return await response.json();
}

// Usage
const jobs = await fetchPropagationJobs(1, {
  status: 'running',
  page_size: 50
});
```

### Monitor Job Progress

```javascript
async function monitorJob(workspaceId, jobId, onUpdate) {
  const interval = setInterval(async () => {
    const response = await fetch(
      `${API_BASE}/workspaces/${workspaceId}/propagation-jobs/${jobId}/`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    const job = await response.json();

    // Update progress
    const progress = (job.processed_count / job.affected_strings_count) * 100;
    onUpdate({
      status: job.status,
      progress,
      processed: job.processed_count,
      total: job.affected_strings_count,
      failed: job.failed_count
    });

    // Stop monitoring if job is complete
    if (['completed', 'partial', 'failed', 'cancelled'].includes(job.status)) {
      clearInterval(interval);
    }
  }, 2000); // Poll every 2 seconds

  return () => clearInterval(interval); // Cleanup function
}

// Usage
const stopMonitoring = await monitorJob(1, 150, (update) => {
  console.log(`Progress: ${update.progress}% (${update.processed}/${update.total})`);
  if (update.failed > 0) {
    console.warn(`Errors: ${update.failed}`);
  }
});
```

### Retry Failed Job

```javascript
async function retryPropagationJob(workspaceId, jobId, reason) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/propagation-jobs/${jobId}/retry/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        retry_failed_only: true,
        reason
      })
    }
  );

  return await response.json();
}

// Usage
const result = await retryPropagationJob(1, 149, 'Fixed constraints');
console.log(`New job ID: ${result.new_job_id}`);
```

### Propagation Errors Display

```javascript
async function fetchPropagationErrors(workspaceId, jobId) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/propagation-errors/?job_id=${jobId}&is_resolved=false`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );

  return await response.json();
}

// Usage
const { results: errors } = await fetchPropagationErrors(1, 149);
errors.forEach(error => {
  console.error(`String ${error.string.id}: ${error.error_message}`);
});
```

---

## Common Use Cases

### 1. Propagation Job Monitor UI

```javascript
function PropagationJobMonitor({ workspaceId, jobId }) {
  const [job, setJob] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const stopMonitoring = monitorJob(workspaceId, jobId, (update) => {
      setJob(update);
      setProgress(update.progress);
    });

    return stopMonitoring;
  }, [workspaceId, jobId]);

  return (
    <div>
      <h3>Propagation Job #{jobId}</h3>
      <ProgressBar value={progress} />
      <p>Status: {job?.status}</p>
      <p>Processed: {job?.processed} / {job?.total}</p>
      {job?.failed > 0 && (
        <p className="error">Failed: {job?.failed}</p>
      )}
    </div>
  );
}
```

### 2. Recent Jobs List

```javascript
function RecentPropagationJobs({ workspaceId }) {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    async function load() {
      const { results } = await fetchPropagationJobs(workspaceId, {
        page_size: 10,
        ordering: '-created'
      });
      setJobs(results);
    }
    load();
  }, [workspaceId]);

  return (
    <table>
      <thead>
        <tr>
          <th>Job Type</th>
          <th>Status</th>
          <th>Strings Affected</th>
          <th>Triggered By</th>
          <th>Started</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map(job => (
          <tr key={job.id}>
            <td>{job.job_type}</td>
            <td><StatusBadge status={job.status} /></td>
            <td>{job.affected_strings_count}</td>
            <td>{job.triggered_by.name}</td>
            <td>{formatDate(job.started_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### 3. Error Resolution Workflow

```javascript
async function resolveError(workspaceId, errorId, resolution) {
  // Mark error as resolved
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/propagation-errors/${errorId}/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        is_resolved: true,
        resolution_notes: resolution
      })
    }
  );

  return await response.json();
}
```

---

## Propagation Triggers

### Automatic Triggers

1. **Dimension Value Change**
   - When a dimension value is updated
   - All strings using that value are updated
   - Can be disabled in settings

2. **Parent String Change**
   - When a parent string is modified
   - All child strings are updated
   - Respects inheritance rules

3. **Rule Pattern Change**
   - When a rule pattern is modified
   - All strings using that rule are regenerated
   - May trigger validation errors

### Manual Triggers

- User can manually trigger propagation for specific strings
- Useful for fixing out-of-sync states
- Requires appropriate permissions

---

## Best Practices

### 1. Monitor Long-Running Jobs

```javascript
// For jobs affecting many strings, provide real-time updates
if (job.affected_strings_count > 100) {
  showProgressModal(job.id);
  monitorJob(workspaceId, job.id, updateProgress);
}
```

### 2. Handle Errors Gracefully

```javascript
// Check for errors after job completion
if (job.status === 'partial' || job.status === 'failed') {
  const errors = await fetchPropagationErrors(workspaceId, job.id);
  showErrorReport(errors);
}
```

### 3. Settings Configuration

```javascript
// For production workspaces, require approval
await updatePropagationSettings(workspaceId, {
  auto_propagate: true,
  require_approval: true,
  notify_on_errors: true
});
```

---

## Notes

- Propagation jobs run asynchronously in background
- Large propagation jobs are batched for performance
- Failed jobs can be retried with same or modified settings
- Propagation respects workspace and project boundaries
- Settings can be configured per workspace
