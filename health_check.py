#!/usr/bin/env python3
"""
Health check script for Railway deployment.
Verifies that the application is fully ready to serve requests.
"""

import os
import sys
import time
import django
import logging
from django.core.management import call_command
from django.db import connection, OperationalError
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection(max_retries=15, initial_delay=2):
    """Test database connection with exponential backoff retry logic."""
    delay = initial_delay
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔍 Database connection attempt {attempt}/{max_retries}...")
            
            # Test basic connection with longer timeout for Railway
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
            logger.info(f"✅ Database connection successful! PostgreSQL version: {version[:50]}...")
            return True
            
        except OperationalError as e:
            error_msg = str(e).lower()
            logger.warning(f"⚠ Database connection failed (attempt {attempt}): {str(e)[:200]}...")
            
            # Check for specific Railway database startup issues
            if 'server closed the connection unexpectedly' in error_msg:
                logger.info("🔄 Railway database appears to be starting up, retrying...")
            elif 'connection failed' in error_msg:
                logger.info("🔄 Database connection failed, likely startup delay...")
            elif 'connection refused' in error_msg:
                logger.info("🔄 Database not accepting connections yet...")
            
            if attempt < max_retries:
                logger.info(f"⏳ Waiting {delay} seconds before retry (exponential backoff)...")
                time.sleep(delay)
                delay = min(delay * 1.5, 30)  # Cap at 30 seconds
            else:
                logger.error("❌ All database connection attempts failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Unexpected database error (attempt {attempt}): {str(e)[:200]}...")
            if attempt < max_retries:
                logger.info(f"⏳ Waiting {delay} seconds before retry...")
                time.sleep(delay)
                delay = min(delay * 1.5, 30)
            else:
                return False
    
    return False


def check_database():
    """Check database connectivity and migrations with Railway-optimized retry logic."""
    # Enhanced database connection test with retries
    if not test_database_connection():
        logger.error("❌ Database connectivity test failed")
        return False
    
    try:
        # Check for unapplied migrations
        from io import StringIO
        
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
        logger.error(f"✗ Migration check failed: {e}")
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

def check_environment():
    """Check required environment variables for Railway deployment."""
    required_vars = [
        'PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE', 'SECRET_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Log Railway-specific info if available
    if os.environ.get('RAILWAY_DEPLOYMENT_ID'):
        logger.info(f"🚂 Railway Deployment ID: {os.environ['RAILWAY_DEPLOYMENT_ID']}")
        logger.info(f"🚂 Railway Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'Unknown')}")
    
    logger.info("✅ All required environment variables present")
    return True


def main():
    """Main health check function with enhanced Railway support."""
    logger.info("🏥 Starting TUX Backend Health Check for Railway...")
    logger.info("=" * 60)
    
    # Check environment first
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.production_settings')
    
    try:
        logger.info("🚀 Initializing Django...")
        django.setup()
        logger.info("✅ Django setup completed successfully")
        
        # Log database configuration for debugging
        db_config = settings.DATABASES['default']
        logger.info(f"📊 Database Config:")
        logger.info(f"  Host: {db_config['HOST']}")
        logger.info(f"  Port: {db_config['PORT']}")
        logger.info(f"  Database: {db_config['NAME']}")
        logger.info(f"  Connect Timeout: {db_config.get('OPTIONS', {}).get('connect_timeout', 'Default')}")
        
    except Exception as e:
        logger.error(f"❌ Django setup failed: {e}")
        sys.exit(1)
    
    logger.info("-" * 60)
    
    # Run all health checks
    checks = [
        ("Database Connection & Migrations", check_database),
        ("Static Files", check_static_files),
        ("Authentication System", check_authentication),
        ("API Schema Generation", check_api_schema),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        logger.info(f"Running {check_name} check...")
        if not check_func():
            failed_checks.append(check_name)
    
    # Summary
    logger.info("=" * 60)
    
    if failed_checks:
        logger.error(f"❌ Health check FAILED. Issues with: {', '.join(failed_checks)}")
        logger.error("🚨 Application is NOT ready for deployment")
        sys.exit(1)
    else:
        logger.info("🎉 ALL HEALTH CHECKS PASSED!")
        logger.info("🚀 Application is ready to serve requests")
        logger.info("✅ Railway deployment can proceed")
        sys.exit(0)

if __name__ == '__main__':
    main()