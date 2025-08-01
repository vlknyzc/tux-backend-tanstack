# String Propagation Enhancement Setup Guide

## Overview

This guide walks you through setting up and migrating to the enhanced string propagation system in the tux-backend. The new system provides comprehensive impact analysis, enhanced propagation control, and background processing capabilities.

## Prerequisites

- Django >= 3.2
- Celery >= 5.0 (for background processing)
- Redis or RabbitMQ (as Celery broker)
- PostgreSQL (recommended for JSON field support)

## Migration Steps

### 1. Database Migration

Run the database migration to create the new propagation models:

```bash
python manage.py migrate master_data 0005_add_propagation_models
```

This creates the following new tables:
- `master_data_propagationjob` - Tracks propagation operations
- `master_data_propagationerror` - Logs propagation errors
- `master_data_propagationsettings` - User/workspace-specific settings

### 2. Configuration Updates

Add the following configuration to your Django settings:

```python
# settings.py

MASTER_DATA_CONFIG = {
    # Enhanced propagation settings
    'AUTO_REGENERATE_STRINGS': True,
    'ENABLE_INHERITANCE_PROPAGATION': True,
    'MAX_INHERITANCE_DEPTH': 10,
    'PROPAGATION_MODE': 'automatic',  # 'automatic', 'manual', 'prompt'
    'PARALLEL_PROPAGATION': True,
    'MAX_PARALLEL_WORKERS': 4,
    'PROPAGATION_TIMEOUT': 300,  # seconds
    'ERROR_HANDLING': 'continue',  # 'continue', 'stop', 'rollback'
    'BACKGROUND_PROCESSING_THRESHOLD': 100,  # strings
    'STRICT_AUTO_REGENERATION': False,
    
    # Field-specific propagation rules
    'FIELD_PROPAGATION_RULES': {
        'dimension_value': 'inherit_always',
        'dimension_value_freetext': 'inherit_if_empty',
        'custom_fields': 'inherit_never',
        'default': 'inherit_always'
    }
}

# Celery configuration for background processing
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'

# Task routing for propagation tasks
CELERY_TASK_ROUTES = {
    'master_data.tasks.propagation_tasks.*': {'queue': 'propagation'},
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/string_propagation.log',
        },
    },
    'loggers': {
        'master_data.string_propagation': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'master_data.propagation_service': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 3. Celery Setup

If you don't already have Celery configured, set it up for background processing:

#### Install Celery and Redis:
```bash
pip install celery redis
```

#### Create celery.py in your project root:
```python
# celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Define queues
app.conf.task_routes = {
    'master_data.tasks.propagation_tasks.*': {'queue': 'propagation'},
}
```

#### Update __init__.py in your project:
```python
# your_project/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

#### Start Celery worker:
```bash
celery -A your_project worker --loglevel=info --queue=propagation
```

### 4. URL Configuration

The new propagation endpoints are automatically included in the master_data URLs. Verify they're accessible:

- `/api/propagation-jobs/` - Propagation job management
- `/api/propagation-errors/` - Error tracking and resolution
- `/api/enhanced-string-details/` - Enhanced string detail operations
- `/api/propagation-settings/` - User propagation preferences

### 5. Legacy Signal Handler Transition

The legacy signal handler has been automatically disabled in favor of the enhanced version. If you have custom signal handlers, review them for compatibility.

The new signal handler provides:
- Better change detection
- Comprehensive error handling
- Audit trail creation
- Background processing integration

## Configuration Options

### Propagation Modes

- **automatic**: All changes trigger propagation automatically
- **manual**: Users must explicitly trigger propagation
- **prompt**: Users are prompted before propagation occurs

### Error Handling Strategies

- **continue**: Continue processing other strings if one fails
- **stop**: Stop entire operation on first error
- **rollback**: Rollback all changes if any error occurs

### Field Propagation Rules

- **inherit_always**: Always propagate changes to children
- **inherit_if_empty**: Only propagate if child field is empty
- **inherit_never**: Never propagate this field

## API Usage Examples

### Impact Analysis

Preview what will be affected before making changes:

```python
import requests

response = requests.post('/api/enhanced-string-details/analyze_impact/', {
    'string_detail_updates': [
        {
            'string_detail_id': 123,
            'dimension_value': 456
        }
    ],
    'max_depth': 10
})

impact = response.json()
print(f"Will affect {impact['summary']['total_affected']} strings")
```

### Dry Run Updates

Test changes without applying them:

```python
response = requests.patch('/api/enhanced-string-details/123/', {
    'dimension_value': 456,
    'dry_run': True,
    'propagate': True,
    'propagation_depth': 5
})

preview = response.json()
if preview['dry_run']:
    print("Preview completed, no changes made")
```

### Batch Updates

Update multiple string details in one operation:

```python
response = requests.put('/api/enhanced-string-details/batch_update/', {
    'updates': [
        {'string_detail_id': 123, 'dimension_value': 456},
        {'string_detail_id': 124, 'dimension_value': 457}
    ],
    'options': {
        'propagate': True,
        'max_depth': 5,
        'error_handling': 'continue'
    }
})

result = response.json()
print(f"Job ID: {result['job_id']}")
```

### Monitor Propagation Jobs

Track background operations:

```python
# List recent jobs
response = requests.get('/api/propagation-jobs/')
jobs = response.json()['results']

# Get job details
job_id = jobs[0]['id']
response = requests.get(f'/api/propagation-jobs/{job_id}/')
job_details = response.json()

print(f"Status: {job_details['status']}")
print(f"Progress: {job_details['progress_percentage']}%")
```

## Performance Considerations

### Background Processing Thresholds

Operations affecting more than `BACKGROUND_PROCESSING_THRESHOLD` strings are automatically queued for background processing. Adjust this based on your system capacity:

```python
MASTER_DATA_CONFIG = {
    'BACKGROUND_PROCESSING_THRESHOLD': 50,  # Lower for faster response
    # or
    'BACKGROUND_PROCESSING_THRESHOLD': 200,  # Higher for more sync operations
}
```

### Celery Queue Management

For high-volume environments, consider dedicated queues:

```python
CELERY_TASK_ROUTES = {
    'master_data.tasks.propagation_tasks.process_large_propagation': {
        'queue': 'propagation_heavy'
    },
    'master_data.tasks.propagation_tasks.analyze_propagation_impact': {
        'queue': 'propagation_light'
    },
}
```

Start workers for specific queues:
```bash
# Heavy processing worker
celery -A your_project worker --queue=propagation_heavy --concurrency=2

# Light analysis worker  
celery -A your_project worker --queue=propagation_light --concurrency=4
```

### Database Optimization

Add indexes for better query performance:

```sql
-- Additional indexes for heavy workloads
CREATE INDEX CONCURRENTLY idx_propagation_job_status_created 
ON master_data_propagationjob (status, created);

CREATE INDEX CONCURRENTLY idx_propagation_error_resolved_created
ON master_data_propagationerror (resolved, created);

CREATE INDEX CONCURRENTLY idx_string_parent_workspace
ON master_data_string (parent_id, workspace_id) WHERE parent_id IS NOT NULL;
```

## Monitoring and Maintenance

### Health Checks

Monitor system health with built-in endpoints:

```python
# Check propagation job success rate
response = requests.get('/api/propagation-jobs/summary/')
stats = response.json()

if stats['success_rate'] < 95:
    alert("Propagation success rate is low")
```

### Error Monitoring

Set up alerts for propagation errors:

```python
# Check for unresolved errors
response = requests.get('/api/propagation-errors/?resolved=false')
errors = response.json()['results']

if len(errors) > 10:
    alert(f"{len(errors)} unresolved propagation errors")
```

### Cleanup Tasks

Schedule regular cleanup of old records:

```python
# In your celery beat schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-propagation-jobs': {
        'task': 'master_data.tasks.propagation_tasks.cleanup_old_propagation_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (30,)  # Keep 30 days of history
    },
}
```

## Troubleshooting

### Common Issues

#### 1. Signal Handler Not Triggering

**Symptoms**: String updates don't trigger propagation
**Solution**: Verify signals are properly imported in apps.py

#### 2. Background Tasks Not Processing

**Symptoms**: Jobs stuck in 'pending' status
**Solutions**:
- Check Celery worker is running
- Verify Redis/broker connection
- Check task routing configuration

#### 3. High Memory Usage

**Symptoms**: Workers consuming excessive memory
**Solutions**:
- Reduce `BACKGROUND_PROCESSING_THRESHOLD`
- Implement chunked processing
- Increase worker recycling frequency

#### 4. Circular Dependency Errors

**Symptoms**: Propagation fails with circular dependency warnings
**Solutions**:
- Review string hierarchy structure
- Implement dependency validation
- Use impact analysis to identify cycles

### Debugging Tips

#### Enable Debug Logging

```python
LOGGING = {
    'loggers': {
        'master_data.string_propagation': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

#### Test with Small Datasets

Use the dry_run feature to test propagation logic:

```python
# Test single update
response = requests.patch('/api/enhanced-string-details/123/', {
    'dimension_value': 456,
    'dry_run': True
})

# Review impact before applying
impact = response.json()['impact_analysis']
```

#### Monitor Performance

Track processing times and identify bottlenecks:

```python
# Check job performance
response = requests.get('/api/propagation-jobs/summary/')
avg_duration = response.json()['average_duration_seconds']

if avg_duration > 30:  # 30 seconds threshold
    investigate_performance_issues()
```

## Migration from Legacy System

### Before Migration

1. **Backup your database** - Critical for rollback capability
2. **Test in staging** - Verify all functionality works as expected
3. **Monitor existing performance** - Establish baseline metrics

### During Migration

1. **Apply migrations during low-traffic periods**
2. **Monitor error logs** during initial operations
3. **Test key workflows** to ensure compatibility

### After Migration

1. **Verify propagation behavior** matches expectations
2. **Set up monitoring** for new metrics and endpoints
3. **Train users** on new features like impact analysis and dry runs

### Rollback Plan

If issues arise, you can disable the enhanced system:

```python
MASTER_DATA_CONFIG = {
    'AUTO_REGENERATE_STRINGS': False,  # Disable all propagation
}
```

Then manually re-enable the legacy signal handler if needed.

## Best Practices

### Development

- Always use dry_run for testing changes
- Use impact analysis before large operations
- Implement proper error handling in client code
- Test with realistic data volumes

### Production

- Monitor propagation job success rates
- Set up alerts for high error rates
- Use appropriate background processing thresholds
- Regular cleanup of old job records

### Performance

- Use batch operations for multiple updates
- Consider off-peak processing for large operations
- Monitor database query performance
- Scale Celery workers based on workload

## Support and Troubleshooting

For issues or questions:

1. Check the logs in `logs/string_propagation.log`
2. Review the propagation job and error records in the admin
3. Use the impact analysis API to understand propagation scope
4. Monitor Celery worker status and queue lengths

## Conclusion

The enhanced string propagation system provides robust, scalable, and controllable string inheritance management. With proper configuration and monitoring, it will significantly improve the reliability and visibility of string operations in your application.