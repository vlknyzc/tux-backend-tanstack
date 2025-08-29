#!/usr/bin/env python3
"""
Robust deployment script for Railway with database connection retry logic.
Handles temporary database connectivity issues during deployment.
"""

import os
import sys
import subprocess
import time
import logging
import django

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command_with_retry(command, max_retries=3, retry_delay=10):
    """
    Run a command with retry logic for database connectivity issues.
    
    Args:
        command (list): Command to run as a list of strings
        max_retries (int): Maximum number of retries
        retry_delay (int): Delay between retries in seconds
        
    Returns:
        bool: True if command succeeded, False otherwise
    """
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Running: {' '.join(command)} (attempt {attempt + 1}/{max_retries + 1})")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"✓ Command succeeded: {' '.join(command)}")
            if result.stdout.strip():
                logger.info(f"Output: {result.stdout.strip()}")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            logger.error(f"✗ Command failed: {error_msg}")
            
            # Check if it's a database connection error
            if any(keyword in error_msg.lower() for keyword in [
                'connection failed', 'server closed the connection', 
                'operationalerror', 'connection refused', 'timeout'
            ]):
                if attempt < max_retries:
                    logger.warning(f"Database connection issue detected. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Max retries exceeded for database operation")
                    return False
            else:
                # Non-database error, don't retry
                logger.error(f"Non-retryable error: {error_msg}")
                return False
    
    return False

def wait_for_database(max_wait=180):  # Increase timeout for Railway
    """Wait for database to be available with Railway-optimized logic."""
    logger.info("🔍 Checking Railway database connectivity...")
    
    # Skip database check in development/local environments
    if os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('local_settings'):
        logger.info("🏠 Local environment detected, skipping database connectivity check")
        return True
    
    # Log Railway deployment info if available
    if os.environ.get('RAILWAY_DEPLOYMENT_ID'):
        logger.info(f"🚂 Railway Deployment ID: {os.environ['RAILWAY_DEPLOYMENT_ID']}")
        # Railway database might take longer during initial deployment
        max_wait = 300  # 5 minutes for Railway deployments
    
    # Initial delay to allow Railway database service to start
    logger.info("⏳ Initial 10-second delay for Railway database startup...")
    time.sleep(10)
    
    check_command = ['python', 'manage.py', 'check', '--database', 'default']
    
    start_time = time.time()
    attempt = 1
    
    while time.time() - start_time < max_wait:
        try:
            logger.info(f"🔍 Database connectivity check (attempt {attempt})...")
            result = subprocess.run(check_command, check=True, capture_output=True, text=True)
            logger.info("✅ Database is available and healthy!")
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            
            # Check for specific Railway database startup patterns
            if 'server closed the connection unexpectedly' in error_msg.lower():
                logger.info("🔄 Railway database is starting up, retrying...")
            elif 'connection failed' in error_msg.lower():
                logger.info("🔄 Database connection failed, likely startup delay...")
            else:
                logger.warning(f"⚠ Database check failed: {error_msg[:200]}...")
            
            # Progressive delay - start with 5 seconds, increase gradually
            delay = min(5 + (attempt // 3) * 2, 15)  # Max 15 seconds
            logger.info(f"⏳ Waiting {delay} seconds before retry...")
            time.sleep(delay)
            attempt += 1
    
    logger.error("❌ Database did not become available within the timeout period")
    return False

def main():
    """Main deployment function with Railway-optimized flow."""
    logger.info("🚂 Starting Railway deployment for TUX Backend...")
    logger.info("=" * 60)
    
    # Set Django settings module (default to production, but allow override)
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'main.production_settings'
    
    # Initialize Django early to ensure settings are loaded
    import django
    django.setup()
    
    # Log deployment environment info
    logger.info(f"⚙️ Django Settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logger.info(f"🚂 Railway Environment: {os.environ['RAILWAY_ENVIRONMENT']}")
    if os.environ.get('RAILWAY_DEPLOYMENT_ID'):
        logger.info(f"🚂 Railway Deployment ID: {os.environ['RAILWAY_DEPLOYMENT_ID']}")
    
    # Log working directory and permissions
    cwd = os.getcwd()
    logger.info(f"📁 Working directory: {cwd}")
    logger.info(f"🔐 Directory writable: {os.access(cwd, os.W_OK)}")
    
    # Step 1: Wait for Railway database to be fully available
    logger.info("✅ STEP 1: Database Connectivity Check")
    if not wait_for_database():
        logger.error("❌ Database is not available. Deployment failed.")
        logger.error("🚨 This might indicate Railway database service issues")
        sys.exit(1)
    
    # Step 2: Run database migrations with retry
    logger.info("✅ STEP 2: Database Migrations")
    if not run_command_with_retry(['python', 'manage.py', 'migrate', '--verbosity=2'], max_retries=5, retry_delay=15):
        logger.error("❌ Migration failed after all retries. Deployment failed.")
        sys.exit(1)
    
    # Step 3: Collect static files with Railway optimization
    logger.info("✅ STEP 3: Static File Collection")
    
    # Ensure static directory exists and is writable
    try:
        from django.conf import settings
        static_root = settings.STATIC_ROOT
        logger.info(f"📁 Creating static files directory: {static_root}")
        os.makedirs(static_root, exist_ok=True)
        
        # Test write permissions
        test_file = os.path.join(static_root, '.railway_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info(f"✅ Static directory is writable: {static_root}")
        
    except Exception as e:
        logger.warning(f"⚠ Static directory setup issue: {e}")
        # Try fallback location
        fallback_static = '/tmp/staticfiles'
        logger.info(f"🔄 Trying fallback static location: {fallback_static}")
        os.makedirs(fallback_static, exist_ok=True)
    
    # Collect static files with enhanced error handling
    collect_command = ['python', 'manage.py', 'collectstatic', '--noinput', '--verbosity=2', '--clear']
    
    if not run_command_with_retry(collect_command, max_retries=3, retry_delay=5):
        logger.warning("⚠ Static file collection failed, but continuing deployment")
        logger.info("🌐 In Railway, static files might be served by proxy/CDN")
        # Don't fail deployment for static files in cloud environments
        pass
    
    # Step 4: Seed platforms data
    logger.info("✅ STEP 4: Platform Data Seeding")
    if not run_command_with_retry(['python', 'manage.py', 'seed_platforms'], max_retries=3, retry_delay=10):
        logger.error("❌ Platform seeding failed. Deployment failed.")
        sys.exit(1)
    
    # Step 5: Create default workspace (allow this to fail gracefully)
    logger.info("✅ STEP 5: Default Workspace Creation")
    if not run_command_with_retry([
        'python', 'manage.py', 'create_workspace', 'Default Workspace', 
        '--admin-email', 'demo@tuxonomy.com', '--create-admin', '--skip-existing'
    ], max_retries=3, retry_delay=10):
        logger.warning("⚠ Workspace creation failed, but this may be expected if it already exists.")
        logger.info("📝 This is not a critical failure for deployment")
    
    logger.info("=" * 60)
    logger.info("🎉 Railway deployment completed successfully!")
    logger.info("🚀 TUX Backend is ready to serve requests")

if __name__ == '__main__':
    main()