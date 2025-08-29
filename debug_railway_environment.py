#!/usr/bin/env python3
"""
Railway Environment Debugging Script
Compares database configuration between working and failing environments.
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


def analyze_railway_environment():
    """Analyze and debug Railway environment configuration."""
    logger.info("🚂 RAILWAY ENVIRONMENT ANALYSIS")
    logger.info("=" * 50)
    
    # Environment variables analysis
    logger.info("📊 Environment Variables:")
    railway_vars = [
        'RAILWAY_DEPLOYMENT_ID', 'RAILWAY_ENVIRONMENT', 'RAILWAY_SERVICE_ID',
        'RAILWAY_VOLUME_MOUNT_PATH', 'RAILWAY_PROJECT_ID'
    ]
    
    for var in railway_vars:
        value = os.environ.get(var, 'NOT SET')
        logger.info(f"  {var}: {value}")
    
    # Database configuration analysis
    logger.info("\n🗄️ Database Configuration:")
    db_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']
    
    for var in db_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'PGPASSWORD':
            # Mask password but show length
            if value != 'NOT SET':
                logger.info(f"  {var}: {'*' * len(value)} (length: {len(value)})")
            else:
                logger.info(f"  {var}: NOT SET")
        else:
            logger.info(f"  {var}: {value}")
    
    # Network analysis
    logger.info("\n🌐 Network Configuration:")
    host = os.environ.get('PGHOST', 'unknown')
    port = os.environ.get('PGPORT', 'unknown')
    
    if host != 'unknown':
        # Check if it's IPv6
        if ':' in host and not host.startswith('['):
            logger.warning(f"  ⚠️ IPv6 host detected: {host}")
            logger.info("  💡 IPv6 hosts should be wrapped in brackets for some clients")
        
        # Check for Railway-specific hostnames
        if 'railway.internal' in host:
            logger.info(f"  ✅ Railway internal network: {host}")
        elif 'railway.app' in host:
            logger.info(f"  ✅ Railway external network: {host}")
        else:
            logger.warning(f"  ⚠️ Non-Railway hostname: {host}")
    
    if port != 'unknown':
        if port == '5432':
            logger.info(f"  ✅ Standard PostgreSQL port: {port}")
        else:
            logger.warning(f"  ⚠️ Non-standard PostgreSQL port: {port}")
    
    return {
        'railway_env': os.environ.get('RAILWAY_ENVIRONMENT'),
        'deployment_id': os.environ.get('RAILWAY_DEPLOYMENT_ID'),
        'db_host': os.environ.get('PGHOST'),
        'db_port': os.environ.get('PGPORT'),
    }


def test_database_connectivity(max_retries=5):
    """Test database connectivity with detailed error reporting."""
    logger.info("\n🔍 Database Connectivity Test:")
    
    django.setup()
    
    from django.db import connection
    from django.conf import settings
    
    # Show Django database config
    db_config = settings.DATABASES['default']
    logger.info("📋 Django Database Configuration:")
    for key, value in db_config.items():
        if key == 'PASSWORD':
            logger.info(f"  {key}: {'*' * len(str(value))}")
        elif key == 'OPTIONS':
            logger.info(f"  {key}: {list(value.keys()) if isinstance(value, dict) else value}")
        else:
            logger.info(f"  {key}: {value}")
    
    # Connection attempts
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"\n🔌 Connection Attempt {attempt}/{max_retries}:")
            
            # Test basic connection
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT version(), current_database(), current_user")
                result = cursor.fetchone()
                
            end_time = time.time()
            
            logger.info("✅ CONNECTION SUCCESS!")
            logger.info(f"  Database Version: {result[0][:60]}...")
            logger.info(f"  Current Database: {result[1]}")
            logger.info(f"  Current User: {result[2]}")
            logger.info(f"  Connection Time: {end_time - start_time:.3f} seconds")
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Connection Failed: {error_msg}")
            
            # Analyze specific error types
            if "server closed the connection unexpectedly" in error_msg:
                logger.warning("  🔧 DIAGNOSIS: Database server terminated connection")
                logger.info("  💡 This often means:")
                logger.info("     - Database service is starting up")
                logger.info("     - Network connectivity issues")
                logger.info("     - Database server overload")
                
            elif "connection refused" in error_msg:
                logger.warning("  🔧 DIAGNOSIS: Database server not accepting connections")
                logger.info("  💡 This often means:")
                logger.info("     - Database service not running")
                logger.info("     - Wrong host/port configuration")
                logger.info("     - Firewall blocking connection")
                
            elif "timeout" in error_msg.lower():
                logger.warning("  🔧 DIAGNOSIS: Connection timeout")
                logger.info("  💡 This often means:")
                logger.info("     - Network latency issues")
                logger.info("     - Database server slow to respond")
                logger.info("     - Need to increase timeout settings")
                
            elif "authentication failed" in error_msg:
                logger.warning("  🔧 DIAGNOSIS: Authentication failed")
                logger.info("  💡 This often means:")
                logger.info("     - Wrong username/password")
                logger.info("     - Database user not properly configured")
                
            if attempt < max_retries:
                wait_time = min(5 * attempt, 30)  # Progressive backoff
                logger.info(f"  ⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    
    logger.error("💥 ALL CONNECTION ATTEMPTS FAILED!")
    return False


def main():
    """Main debugging function."""
    logger.info("🚂 Railway Environment Debugging Tool")
    logger.info("=" * 50)
    
    # Analyze environment
    env_info = analyze_railway_environment()
    
    # Test database connectivity
    success = test_database_connectivity()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📋 SUMMARY:")
    logger.info(f"  Railway Environment: {env_info['railway_env']}")
    logger.info(f"  Deployment ID: {env_info['deployment_id']}")
    logger.info(f"  Database Host: {env_info['db_host']}")
    logger.info(f"  Database Port: {env_info['db_port']}")
    logger.info(f"  Database Connection: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        logger.info("🎉 Environment is ready for deployment!")
        sys.exit(0)
    else:
        logger.error("💥 Environment has issues that need resolution!")
        sys.exit(1)


if __name__ == '__main__':
    main()