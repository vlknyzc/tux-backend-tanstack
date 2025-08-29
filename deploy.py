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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command_with_retry(command, max_retries=3, retry_delay=5):
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

def wait_for_database(max_wait=60):
    """Wait for database to be available."""
    logger.info("Checking database connectivity...")
    
    # Skip database check in development/local environments
    if os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('local_settings'):
        logger.info("Local environment detected, skipping database connectivity check")
        return True
    
    check_command = ['python', 'manage.py', 'check', '--database', 'default']
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            subprocess.run(check_command, check=True, capture_output=True, text=True)
            logger.info("✓ Database is available")
            return True
        except subprocess.CalledProcessError:
            logger.info("Database not ready, waiting...")
            time.sleep(2)
    
    logger.error("Database did not become available within the timeout period")
    return False

def main():
    """Main deployment function."""
    logger.info("Starting Railway deployment...")
    
    # Set Django settings module (default to production, but allow override)
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'main.production_settings'
    
    # Step 1: Wait for database to be available
    if not wait_for_database():
        logger.error("Database is not available. Deployment failed.")
        sys.exit(1)
    
    # Step 2: Run migrations with retry
    logger.info("Running database migrations...")
    if not run_command_with_retry(['python', 'manage.py', 'migrate'], max_retries=5, retry_delay=10):
        logger.error("Migration failed after all retries. Deployment failed.")
        sys.exit(1)
    
    # Step 3: Collect static files (usually doesn't fail, but include for completeness)
    logger.info("Collecting static files...")
    if not run_command_with_retry(['python', 'manage.py', 'collectstatic', '--noinput'], max_retries=2):
        logger.error("Static file collection failed. Deployment failed.")
        sys.exit(1)
    
    # Step 4: Seed platforms (with retry for database operations)
    logger.info("Seeding platforms...")
    if not run_command_with_retry(['python', 'manage.py', 'seed_platforms'], max_retries=3):
        logger.error("Platform seeding failed. Deployment failed.")
        sys.exit(1)
    
    # Step 5: Create default workspace (with retry)
    logger.info("Creating default workspace...")
    if not run_command_with_retry([
        'python', 'manage.py', 'create_workspace', 'Default Workspace', 
        '--admin-email', 'demo@tuxonomy.com', '--create-admin', '--skip-existing'
    ], max_retries=3):
        logger.warning("Workspace creation failed, but this may be expected if it already exists.")
    
    logger.info("🎉 Deployment completed successfully!")

if __name__ == '__main__':
    main()