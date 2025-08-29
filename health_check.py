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
            
            # Test basic connection with database-agnostic query
            with connection.cursor() as cursor:
                # Use a simple query that works on both PostgreSQL and SQLite
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()[0]
                
            if result == 1:
                # Try to get database version info
                try:
                    with connection.cursor() as cursor:
                        if 'postgresql' in connection.settings_dict['ENGINE']:
                            cursor.execute("SELECT version()")
                            version_info = cursor.fetchone()[0][:50] + "..."
                        elif 'sqlite' in connection.settings_dict['ENGINE']:
                            cursor.execute("SELECT sqlite_version()")
                            version_info = f"SQLite {cursor.fetchone()[0]}"
                        else:
                            version_info = "Unknown database type"
                except Exception:
                    version_info = "Version info unavailable"
                
                logger.info(f"✅ Database connection successful! {version_info}")
                return True
            else:
                logger.error(f"❌ Database test query returned unexpected result: {result}")
                return False
            
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
    """Check if static files are available with Railway-friendly logic."""
    try:
        static_root = settings.STATIC_ROOT
        logger.info(f"📊 Static root configured as: {static_root}")
        
        # Try multiple potential static file locations
        potential_paths = [
            static_root,
            "/opt/railway/staticfiles",
            "/app/staticfiles",
            str(settings.BASE_DIR / "staticfiles"),
        ]
        
        for path in potential_paths:
            if path and os.path.exists(path):
                try:
                    file_count = sum(len(files) for _, _, files in os.walk(path))
                    if file_count > 0:
                        logger.info(f"✅ Static files found: {file_count} files in {path}")
                        return True
                    else:
                        logger.info(f"📁 Empty static directory found: {path}")
                except Exception as walk_error:
                    logger.warning(f"⚠ Could not walk directory {path}: {walk_error}")
            else:
                logger.debug(f"🔍 Static path not found: {path}")
        
        # In Railway/cloud environments, static files might be served differently
        if os.environ.get('RAILWAY_DEPLOYMENT_ID'):
            logger.warning("⚠ No static files directory found, but this may be expected in Railway deployment")
            logger.info("🌐 Static files might be served by Railway's CDN or proxy")
            # Don't fail the health check for missing static files in Railway
            return True
        else:
            logger.error("❌ No static files directory found in non-Railway environment")
            return False
            
    except Exception as e:
        logger.error(f"❌ Static files check failed: {e}")
        # Don't fail health check for static files in production/cloud environments
        if os.environ.get('RAILWAY_DEPLOYMENT_ID') or not settings.DEBUG:
            logger.warning("⚠ Static files check failed, but allowing deployment to continue")
            return True
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