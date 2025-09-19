# TUX Backend Monitoring & Logging Implementation Guide

## Overview

This document provides a comprehensive implementation guide for monitoring and logging infrastructure for the TUX Backend Django REST API. The system handles multi-tenant SaaS operations with complex string propagation logic and requires robust monitoring for performance, security, and business intelligence.

## Current Architecture Analysis

### Existing Infrastructure

- **Framework**: Django REST Framework with multi-tenant architecture
- **Database**: PostgreSQL (production and development)
- **Deployment**: Railway platform
- **Authentication**: JWT-based with workspace isolation
- **Key Business Logic**: String propagation, dimension management, rule processing

### Current Logging Setup

- Basic console logging in production
- Separate log levels for Django core, database, and master_data app
- No structured logging or centralized log aggregation

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

1. **Error Tracking with Sentry**
2. **Structured Logging**
3. **Basic Health Checks**
4. **Request Monitoring Middleware**

### Phase 2: Metrics Collection (Week 3-4)

1. **Prometheus Metrics Integration**
2. **Custom Business Metrics**
3. **Database Performance Monitoring**
4. **Background Job Monitoring**

### Phase 3: Visualization & Alerting (Week 5-6)

1. **Grafana Dashboard Setup**
2. **Alert Rules Configuration**
3. **Log Aggregation (ELK Stack or similar)**
4. **Performance Optimization Insights**

## Detailed Implementation

### 1. Sentry Integration

#### Installation

```bash
pip install sentry-sdk[django]
```

#### Configuration (settings)

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Sentry configuration
sentry_logging = LoggingIntegration(
    level=logging.INFO,        # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
)

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(
            transaction_style='url',
            middleware_spans=True,
            signals_spans=False,
        ),
        sentry_logging,
    ],
    traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
    send_default_pii=False,  # Don't send personal data
    environment=os.environ.get("ENVIRONMENT", "development"),
    before_send=filter_sensitive_data,  # Custom function to filter sensitive data
)

def filter_sensitive_data(event, hint):
    """Filter sensitive data from Sentry events"""
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        event['request']['headers'].pop('Authorization', None)
        event['request']['headers'].pop('Cookie', None)

    # Add workspace context
    if hasattr(event, 'user') and 'workspace_id' in event.get('extra', {}):
        event.setdefault('tags', {})['workspace'] = event['extra']['workspace_id']

    return event
```

### 2. Structured Logging Implementation

#### Custom Logging Formatter

```python
# main/logging.py
import json
import logging
from datetime import datetime
from django.utils.timezone import now

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    def format(self, record):
        log_entry = {
            'timestamp': now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add extra fields
        if hasattr(record, 'workspace_id'):
            log_entry['workspace_id'] = record.workspace_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

# Enhanced logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'main.logging.JSONFormatter',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/tux-backend.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'tux.monitoring': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'tux.business': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'tux.performance': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

### 3. Request Monitoring Middleware

```python
# main/middleware.py
import time
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('tux.monitoring')
performance_logger = logging.getLogger('tux.performance')

class MonitoringMiddleware(MiddlewareMixin):
    """
    Middleware for request monitoring and performance tracking
    """

    def process_request(self, request):
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())

        # Add request ID to headers for tracing
        request.META['HTTP_X_REQUEST_ID'] = request.request_id

        # Extract workspace info
        workspace_id = self.get_workspace_id(request)
        request.workspace_id = workspace_id

        logger.info(
            "Request started",
            extra={
                'request_id': request.request_id,
                'method': request.method,
                'path': request.path,
                'workspace_id': workspace_id,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self.get_client_ip(request),
            }
        )

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000  # Convert to ms

            # Determine if this is a slow request
            is_slow = duration > 1000  # 1 second threshold
            log_level = logging.WARNING if is_slow else logging.INFO

            performance_logger.log(
                log_level,
                f"Request completed in {duration:.2f}ms",
                extra={
                    'request_id': getattr(request, 'request_id', ''),
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'workspace_id': getattr(request, 'workspace_id', ''),
                    'user_id': request.user.id if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                    'is_slow_request': is_slow,
                }
            )

        # Add request ID to response headers for tracing
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id

        return response

    def process_exception(self, request, exception):
        logger.error(
            f"Request failed with exception: {str(exception)}",
            extra={
                'request_id': getattr(request, 'request_id', ''),
                'method': request.method,
                'path': request.path,
                'workspace_id': getattr(request, 'workspace_id', ''),
                'exception_type': type(exception).__name__,
            },
            exc_info=True
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_workspace_id(self, request):
        # Extract workspace from URL, headers, or user context
        # Implementation depends on your workspace detection logic
        if hasattr(request, 'user') and hasattr(request.user, 'current_workspace'):
            return request.user.current_workspace.id
        return None
```

### 4. Health Check Endpoints

```python
# master_data/views/health_views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import time

def health_check(request):
    """
    Comprehensive health check endpoint
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'services': {}
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['services']['database'] = {'status': 'healthy', 'response_time': 'fast'}
    except Exception as e:
        health_status['services']['database'] = {'status': 'unhealthy', 'error': str(e)}
        health_status['status'] = 'unhealthy'

    # Cache check (if using Redis)
    try:
        cache.set('health_check', 'ok', 30)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_status['services']['cache'] = {'status': 'healthy'}
        else:
            health_status['services']['cache'] = {'status': 'unhealthy', 'error': 'Cache write/read failed'}
    except Exception as e:
        health_status['services']['cache'] = {'status': 'unhealthy', 'error': str(e)}

    # Add application-specific checks
    health_status['services']['string_propagation'] = check_propagation_service()
    health_status['services']['workspace_isolation'] = check_workspace_isolation()

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)

def readiness_check(request):
    """
    Kubernetes readiness probe endpoint
    """
    # Check if application is ready to serve traffic
    checks = [
        check_database_migrations(),
        check_required_environment_variables(),
        check_workspace_configuration(),
    ]

    if all(checks):
        return JsonResponse({'status': 'ready'})
    else:
        return JsonResponse({'status': 'not_ready'}, status=503)

def liveness_check(request):
    """
    Kubernetes liveness probe endpoint
    """
    # Simple check that the application is running
    return JsonResponse({'status': 'alive'})
```

### 5. Prometheus Metrics Integration

```python
# requirements.txt addition
# django-prometheus==2.2.0
# prometheus-client==0.14.1

# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    # ... your other apps
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... your other middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Custom metrics
# master_data/metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time

# Custom metrics registry
registry = CollectorRegistry()

# Business metrics
string_generations = Counter(
    'tux_string_generations_total',
    'Total number of string generations',
    ['workspace_id', 'status'],
    registry=registry
)

propagation_jobs = Counter(
    'tux_propagation_jobs_total',
    'Total number of propagation jobs',
    ['workspace_id', 'status'],
    registry=registry
)

propagation_duration = Histogram(
    'tux_propagation_duration_seconds',
    'Time spent on string propagation',
    ['workspace_id'],
    registry=registry
)

workspace_activity = Gauge(
    'tux_workspace_active_users',
    'Number of active users per workspace',
    ['workspace_id'],
    registry=registry
)

dimension_catalog_queries = Counter(
    'tux_dimension_catalog_queries_total',
    'Total dimension catalog queries',
    ['workspace_id', 'cache_hit'],
    registry=registry
)

# Usage in services
class MetricsCollector:
    @staticmethod
    def record_string_generation(workspace_id, success=True):
        status = 'success' if success else 'error'
        string_generations.labels(workspace_id=workspace_id, status=status).inc()

    @staticmethod
    def record_propagation_job(workspace_id, duration_seconds, success=True):
        status = 'success' if success else 'error'
        propagation_jobs.labels(workspace_id=workspace_id, status=status).inc()
        propagation_duration.labels(workspace_id=workspace_id).observe(duration_seconds)

    @staticmethod
    def record_dimension_query(workspace_id, cache_hit=False):
        cache_status = 'hit' if cache_hit else 'miss'
        dimension_catalog_queries.labels(workspace_id=workspace_id, cache_hit=cache_status).inc()
```

### 6. Business Logic Monitoring

```python
# master_data/services/monitoring_service.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.db.models import Count, Avg
from .metrics import MetricsCollector

logger = logging.getLogger('tux.business')

class BusinessMonitoringService:
    """
    Service for monitoring business-specific metrics and events
    """

    @staticmethod
    def log_string_generation(workspace_id: str, rule_id: str, success: bool,
                            generation_time: float, error_message: Optional[str] = None):
        """Log string generation events"""
        logger.info(
            "String generation completed",
            extra={
                'workspace_id': workspace_id,
                'rule_id': rule_id,
                'success': success,
                'generation_time_ms': generation_time * 1000,
                'error_message': error_message,
                'event_type': 'string_generation'
            }
        )

        # Update metrics
        MetricsCollector.record_string_generation(workspace_id, success)

    @staticmethod
    def log_propagation_job(workspace_id: str, job_id: str, affected_strings: int,
                           duration: float, success: bool, error_details: Optional[Dict] = None):
        """Log propagation job execution"""
        logger.info(
            f"Propagation job completed - {affected_strings} strings affected",
            extra={
                'workspace_id': workspace_id,
                'job_id': job_id,
                'affected_strings': affected_strings,
                'duration_seconds': duration,
                'success': success,
                'error_details': error_details,
                'event_type': 'propagation_job'
            }
        )

        # Update metrics
        MetricsCollector.record_propagation_job(workspace_id, duration, success)

    @staticmethod
    def log_dimension_access(workspace_id: str, dimension_id: str,
                           operation: str, cache_hit: bool = False):
        """Log dimension catalog access"""
        logger.debug(
            f"Dimension {operation} operation",
            extra={
                'workspace_id': workspace_id,
                'dimension_id': dimension_id,
                'operation': operation,
                'cache_hit': cache_hit,
                'event_type': 'dimension_access'
            }
        )

        # Update metrics
        MetricsCollector.record_dimension_query(workspace_id, cache_hit)

    @staticmethod
    def log_workspace_activity(workspace_id: str, user_id: str, activity_type: str):
        """Log user activity within workspace"""
        logger.info(
            f"Workspace activity: {activity_type}",
            extra={
                'workspace_id': workspace_id,
                'user_id': user_id,
                'activity_type': activity_type,
                'event_type': 'workspace_activity'
            }
        )

    @staticmethod
    def generate_performance_report(workspace_id: str, days: int = 7) -> Dict[str, Any]:
        """Generate performance report for a workspace"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # This would query your metrics storage (Prometheus, database, etc.)
        report = {
            'workspace_id': workspace_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'metrics': {
                'string_generations': 0,  # Query from metrics
                'propagation_jobs': 0,
                'average_response_time': 0,
                'error_rate': 0,
                'cache_hit_rate': 0
            }
        }

        logger.info(
            "Performance report generated",
            extra={
                'workspace_id': workspace_id,
                'report': report,
                'event_type': 'performance_report'
            }
        )

        return report
```

### 7. Alert Configuration

```yaml
# alerts/tux-backend-alerts.yml
groups:
  - name: tux-backend
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: rate(django_http_responses_total_by_status_view_method{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      # Slow Response Times
      - alert: SlowResponseTimes
        expr: django_http_request_duration_seconds{quantile="0.95"} > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times detected"
          description: "95th percentile response time is {{ $value }} seconds"

      # String Propagation Job Failures
      - alert: PropagationJobFailures
        expr: rate(tux_propagation_jobs_total{status="error"}[10m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Propagation job failures detected"
          description: "Propagation job failure rate is {{ $value }} per second"

      # Database Connection Issues
      - alert: DatabaseConnectionIssues
        expr: up{job="tux-backend-health"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
          description: "Cannot connect to database for 2+ minutes"

      # Memory Usage
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 512
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}MB"
```

### 8. Dashboard Configuration (Grafana)

```json
{
  "dashboard": {
    "title": "TUX Backend Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(django_http_requests_total[5m])",
            "legendFormat": "{{method}} {{view}}"
          }
        ]
      },
      {
        "title": "Response Times",
        "targets": [
          {
            "expr": "django_http_request_duration_seconds{quantile=\"0.95\"}",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "String Generation Rate by Workspace",
        "targets": [
          {
            "expr": "rate(tux_string_generations_total[5m])",
            "legendFormat": "{{workspace_id}} - {{status}}"
          }
        ]
      },
      {
        "title": "Propagation Job Performance",
        "targets": [
          {
            "expr": "tux_propagation_duration_seconds",
            "legendFormat": "{{workspace_id}}"
          }
        ]
      },
      {
        "title": "Cache Performance",
        "targets": [
          {
            "expr": "rate(tux_dimension_catalog_queries_total[5m])",
            "legendFormat": "{{cache_hit}}"
          }
        ]
      }
    ]
  }
}
```

## Security Considerations

### 1. Data Privacy

- Filter sensitive data from logs (passwords, tokens, personal information)
- Implement log retention policies
- Ensure GDPR compliance for user data in logs

### 2. Access Control

- Restrict access to monitoring dashboards
- Use role-based access for different monitoring levels
- Secure API keys and monitoring credentials

### 3. Log Security

- Encrypt logs in transit and at rest
- Implement log integrity verification
- Monitor for log tampering attempts

## Performance Considerations

### 1. Monitoring Overhead

- Use sampling for high-volume metrics
- Implement circuit breakers for monitoring failures
- Monitor the monitoring system performance

### 2. Storage Management

- Implement log rotation and retention policies
- Use appropriate storage tiers for different log types
- Compress historical data

### 3. Network Impact

- Batch metric exports when possible
- Use local buffering for metrics collection
- Implement backpressure handling

## Testing the Implementation

### 1. Unit Tests for Monitoring Components

```python
# tests/test_monitoring.py
from django.test import TestCase, RequestFactory
from main.middleware import MonitoringMiddleware
import json

class MonitoringMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = MonitoringMiddleware()

    def test_request_id_generation(self):
        request = self.factory.get('/api/v1/test/')
        self.middleware.process_request(request)

        self.assertTrue(hasattr(request, 'request_id'))
        self.assertTrue(hasattr(request, 'start_time'))

    def test_performance_logging(self):
        request = self.factory.get('/api/v1/test/')
        self.middleware.process_request(request)

        # Simulate slow request
        import time
        time.sleep(0.1)

        response = self.middleware.process_response(request, type('Response', (), {'status_code': 200})())

        # Check if X-Request-ID is in response
        self.assertIn('X-Request-ID', response)
```

### 2. Load Testing with Monitoring

```python
# scripts/load_test_with_monitoring.py
import requests
import time
import concurrent.futures
import logging

def make_request(url, headers):
    start_time = time.time()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        duration = time.time() - start_time
        return {
            'status_code': response.status_code,
            'duration': duration,
            'success': response.status_code < 400
        }
    except Exception as e:
        return {
            'status_code': 0,
            'duration': time.time() - start_time,
            'success': False,
            'error': str(e)
        }

def load_test():
    url = 'http://localhost:8000/api/v1/health/'
    headers = {'Authorization': 'JWT your-test-token'}

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, url, headers) for _ in range(100)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    # Analyze results
    success_rate = sum(1 for r in results if r['success']) / len(results)
    avg_duration = sum(r['duration'] for r in results) / len(results)

    print(f"Success Rate: {success_rate:.2%}")
    print(f"Average Duration: {avg_duration:.3f}s")

if __name__ == '__main__':
    load_test()
```

## Maintenance and Operations

### 1. Regular Monitoring Tasks

- Weekly performance report generation
- Monthly log analysis and cleanup
- Quarterly alert rule review and optimization
- Annual security audit of monitoring infrastructure

### 2. Troubleshooting Guide

- Common monitoring issues and solutions
- Performance debugging workflows
- Log analysis techniques for different problem types

### 3. Scaling Considerations

- Horizontal scaling of monitoring components
- Multi-region monitoring setup
- Load balancing for monitoring endpoints

## Integration with CI/CD

### 1. Monitoring Configuration as Code

```yaml
# .github/workflows/monitoring.yml
name: Deploy Monitoring Configuration
on:
  push:
    paths:
      - "monitoring/**"
      - "alerts/**"

jobs:
  deploy-monitoring:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Grafana Dashboards
        run: |
          # Deploy dashboard configurations
          # Update alert rules
          # Restart monitoring services if needed
```

### 2. Monitoring Metrics in CI/CD

- Performance regression detection
- Error rate monitoring in deployments
- Automated rollback triggers based on monitoring data

## Cost Optimization

### 1. Monitoring Cost Management

- Log level optimization in production
- Metric retention policies
- Efficient data storage strategies

### 2. Resource Optimization

- Monitor monitoring resource usage
- Optimize query performance for dashboards
- Use caching for frequently accessed metrics

This implementation guide provides a comprehensive foundation for monitoring your TUX Backend. Start with Phase 1 (Sentry + basic logging) and gradually implement additional phases based on your operational needs and priorities.
