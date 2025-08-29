#!/usr/bin/env python3
"""
Health check script for Railway deployment.
Verifies that the application is fully ready to serve requests.
"""

import os
import sys
import django
import logging
from django.core.management import call_command
from django.db import connection
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database():
    """Check database connectivity and migrations."""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        logger.info("✓ Database connection is healthy")
        
        # Check for unapplied migrations
        from django.core.management import execute_from_command_line
        from io import StringIO
        import sys
        
        # Capture output from showmigrations
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            call_command('showmigrations', '--plan')
            migrations_output = mystdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        if '[ ]' in migrations_output:
            logger.warning("⚠ There are unapplied migrations")
            return False
        else:
            logger.info("✓ All migrations are applied")
            return True
            
    except Exception as e:
        logger.error(f"✗ Database check failed: {e}")
        return False

def check_static_files():
    """Check if static files are available."""
    try:
        static_root = settings.STATIC_ROOT
        if static_root and os.path.exists(static_root):
            file_count = sum(len(files) for _, _, files in os.walk(static_root))
            logger.info(f"✓ Static files available: {file_count} files in {static_root}")
            return True
        else:
            logger.warning("⚠ Static files directory not found")
            return False
    except Exception as e:
        logger.error(f"✗ Static files check failed: {e}")
        return False

def check_authentication():
    """Check if authentication classes can be imported."""
    try:
        from users.authentication import CustomJWTAuthentication
        logger.info("✓ Authentication classes import successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Authentication import failed: {e}")
        return False

def check_api_schema():
    """Check if API schema can be generated."""
    try:
        from drf_spectacular.openapi import AutoSchema
        logger.info("✓ API schema generation is available")
        return True
    except ImportError as e:
        logger.error(f"✗ API schema check failed: {e}")
        return False

def main():
    """Main health check function."""
    logger.info("Starting application health check...")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.production_settings')
    
    try:
        django.setup()
        logger.info("✓ Django setup completed successfully")
    except Exception as e:
        logger.error(f"✗ Django setup failed: {e}")
        sys.exit(1)
    
    # Run all health checks
    checks = [
        ("Database", check_database),
        ("Static Files", check_static_files),
        ("Authentication", check_authentication),
        ("API Schema", check_api_schema),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        logger.info(f"Running {check_name} check...")
        if not check_func():
            failed_checks.append(check_name)
    
    # Summary
    if failed_checks:
        logger.error(f"❌ Health check failed. Issues with: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        logger.info("🎉 All health checks passed! Application is ready.")
        sys.exit(0)

if __name__ == '__main__':
    main()