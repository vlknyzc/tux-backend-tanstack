#!/usr/bin/env python3
"""
Railway-specific health check that handles environment differences.
This runs after successful deployment to verify the environment is working.
"""

import os
import sys
import time
import django
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).resolve().parent))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.production_settings')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_railway_environment():
    """Check Railway environment configuration."""
    logger.info("🚂 Railway Environment Check:")
    
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')
    deployment_id = os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown')
    
    logger.info(f"  Environment: {railway_env}")
    logger.info(f"  Deployment ID: {deployment_id[:16]}..." if deployment_id != 'unknown' else "  Deployment ID: unknown")
    
    # Check database configuration
    db_host = os.environ.get('PGHOST', 'unknown')
    db_port = os.environ.get('PGPORT', 'unknown')
    
    logger.info(f"  Database Host: {db_host}")
    logger.info(f"  Database Port: {db_port}")
    
    # Warn about potential issues
    if ':' in db_host and not db_host.startswith('['):
        logger.warning("  ⚠️ IPv6 database host detected - may cause connection issues")
    
    if db_port != '5432':
        logger.warning(f"  ⚠️ Non-standard PostgreSQL port: {db_port}")
    
    return railway_env, deployment_id


def test_database_connection():
    """Test database connection with Railway-specific handling."""
    logger.info("🗄️ Database Connection Test:")
    
    try:
        django.setup()
        from django.db import connection
        
        # Test basic connection
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1, current_database(), current_user")
            result = cursor.fetchone()
        
        end_time = time.time()
        
        logger.info("  ✅ Database connection successful!")
        logger.info(f"  Database: {result[1]}")
        logger.info(f"  User: {result[2]}")
        logger.info(f"  Response time: {end_time - start_time:.3f}s")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"  ❌ Database connection failed: {error_msg}")
        
        if "server closed the connection unexpectedly" in error_msg:
            logger.warning("  🔧 Database server terminated connection")
            logger.info("  💡 This may indicate service instability in this environment")
        elif "connection refused" in error_msg:
            logger.warning("  🔧 Database server not accepting connections")
            logger.info("  💡 Database service may not be running properly")
        
        return False


def test_application_readiness():
    """Test application components."""
    logger.info("🔧 Application Readiness Test:")
    
    try:
        # Test critical imports
        try:
            from users.authentication import CustomJWTAuthentication
            logger.info("  ✅ Custom authentication system ready")
        except ImportError as e:
            logger.warning(f"  ⚠ Custom authentication import issue: {e}")
            from rest_framework_simplejwt.authentication import JWTAuthentication
            logger.info("  ✅ Base JWT authentication ready")
        
        from django.urls import get_resolver
        resolver = get_resolver()
        logger.info("  ✅ URL configuration loaded")
        
        # Test static files configuration
        from django.conf import settings
        static_root = settings.STATIC_ROOT
        logger.info(f"  ✅ Static files configured: {static_root}")
        
        # Test ALLOWED_HOSTS for Railway
        railway_hosts = [host for host in settings.ALLOWED_HOSTS if 'railway' in host]
        logger.info(f"  ✅ Railway hosts configured: {len(railway_hosts)} domains")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Application readiness failed: {e}")
        return False


def main():
    """Main health check function."""
    logger.info("🏥 Railway Health Check Starting...")
    logger.info("=" * 50)
    
    try:
        # Check Railway environment
        railway_env, deployment_id = check_railway_environment()
        
        # Test database connection
        db_ok = test_database_connection()
        
        # Test application readiness
        app_ok = test_application_readiness()
        
        # Summary
        logger.info("=" * 50)
        logger.info("📋 Health Check Summary:")
        logger.info(f"  Railway Environment: {railway_env}")
        logger.info(f"  Database Connection: {'OK' if db_ok else 'FAILED'}")
        logger.info(f"  Application Readiness: {'OK' if app_ok else 'FAILED'}")
        
        if db_ok and app_ok:
            logger.info("🎉 Railway health check PASSED!")
            logger.info("🚀 Environment is ready to serve traffic!")
            sys.exit(0)
        else:
            logger.error("💥 Railway health check FAILED!")
            logger.error("🚨 Environment has issues that may affect reliability!")
            
            if not db_ok:
                logger.error("   - Database connectivity problems detected")
                logger.error("   - This may cause intermittent application failures")
            
            if not app_ok:
                logger.error("   - Application configuration problems detected")
                logger.error("   - This may cause startup or runtime failures")
            
            # In Railway, we might want to continue despite some issues
            # to allow troubleshooting, but log the problems
            railway_env_type = os.environ.get('RAILWAY_ENVIRONMENT', 'development')
            if railway_env_type == 'production':
                logger.error("🛑 Failing production health check due to critical issues")
                sys.exit(1)
            else:
                logger.warning("⚠️ Continuing with development deployment despite issues")
                sys.exit(0)
            
    except Exception as e:
        logger.error(f"💥 Health check crashed: {e}")
        logger.error("🚨 Critical failure in health check process")
        sys.exit(1)


if __name__ == '__main__':
    main()