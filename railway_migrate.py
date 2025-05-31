#!/usr/bin/env python3
"""
One-time script to fix the migration issue on Railway
Run this as a one-time job or service
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Add the project directory to Python path
sys.path.append('/app')  # Railway typically puts code in /app

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

if __name__ == '__main__':
    # Execute the migration command
    execute_from_command_line(
        ['manage.py', 'migrate', 'master_data', '0003', '--fake'])
    print("Migration 0003 marked as applied successfully!")
