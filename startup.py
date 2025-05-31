#!/usr/bin/env python3
"""
Startup script for Railway deployment
Handles migration fixes before starting the main application
"""

import os
import subprocess
import sys


def run_migration_fix():
    """Run the migration fix if environment variable is set"""
    if os.environ.get('RUN_MIGRATION_FIX') == 'true':
        print("Running migration fix...")
        try:
            result = subprocess.run([
                'python', 'manage.py', 'migrate',
                'master_data', '0003', '--fake'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("Migration fix completed successfully!")
                print(result.stdout)
            else:
                print("Migration fix failed:")
                print(result.stderr)

        except Exception as e:
            print(f"Error running migration fix: {e}")


if __name__ == '__main__':
    # Run migration fix if requested
    run_migration_fix()

    # Start the main application
    os.system('gunicorn main.wsgi')
