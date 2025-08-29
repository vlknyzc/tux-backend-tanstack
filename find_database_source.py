#!/usr/bin/env python3
"""
Find the source of the database connection string.
This will show you exactly where that IPv6 address is coming from.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).resolve().parent))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.production_settings')

def analyze_database_source():
    """Analyze where the database configuration is coming from."""
    print("🔍 DATABASE SOURCE ANALYSIS")
    print("=" * 50)
    
    # 1. Check raw environment variables
    print("📊 RAW ENVIRONMENT VARIABLES:")
    db_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']
    
    for var in db_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'PGPASSWORD':
            if value != 'NOT SET':
                print(f"  {var}: {'*' * 8} (length: {len(value)})")
            else:
                print(f"  {var}: NOT SET")
        else:
            print(f"  {var}: {value}")
            
            # Check if this is where the IPv6 address is coming from
            if 'bea8:8f79' in str(value):
                print(f"  🚨 FOUND IPv6 ADDRESS IN {var}! ^^^")
    
    # 2. Check for DATABASE_URL (common Railway pattern)
    database_url = os.environ.get('DATABASE_URL', 'NOT SET')
    print(f"\nDATABASE_URL: {database_url}")
    if 'bea8:8f79' in str(database_url):
        print("  🚨 FOUND IPv6 ADDRESS IN DATABASE_URL! ^^^")
    
    # 3. Check other Railway database variables
    print("\n🚂 RAILWAY-SPECIFIC VARIABLES:")
    railway_db_vars = [
        'DATABASE_URL', 
        'DATABASE_PRIVATE_URL',
        'DATABASE_PUBLIC_URL',
        'POSTGRES_URL',
        'POSTGRES_PRIVATE_URL',
        'POSTGRES_PUBLIC_URL'
    ]
    
    for var in railway_db_vars:
        value = os.environ.get(var, 'NOT SET')
        if value != 'NOT SET':
            # Mask the password part but show the host
            if '://' in value and '@' in value:
                try:
                    # Parse URL to extract host/port
                    parts = value.split('://', 1)[1]  # Remove protocol
                    auth_host = parts.split('/', 1)[0]  # Get user:pass@host:port part
                    if '@' in auth_host:
                        host_port = auth_host.split('@', 1)[1]  # Get host:port
                        print(f"  {var}: postgresql://***@{host_port}/***")
                        
                        if 'bea8:8f79' in host_port:
                            print(f"  🚨 FOUND IPv6 ADDRESS IN {var}! ^^^")
                    else:
                        print(f"  {var}: {value[:30]}...")
                except:
                    print(f"  {var}: {value[:30]}...")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: NOT SET")
    
    # 4. Check what Django actually uses
    print("\n🐍 DJANGO DATABASE CONFIGURATION:")
    try:
        django.setup()
        from django.conf import settings
        
        db_config = settings.DATABASES['default']
        print(f"  ENGINE: {db_config.get('ENGINE')}")
        print(f"  HOST: {db_config.get('HOST')}")
        print(f"  PORT: {db_config.get('PORT')}")
        print(f"  NAME: {db_config.get('NAME')}")
        print(f"  USER: {db_config.get('USER')}")
        print(f"  PASSWORD: {'*' * len(str(db_config.get('PASSWORD', '')))} (length: {len(str(db_config.get('PASSWORD', '')))})")
        
        # Check if IPv6 is in Django config
        if 'bea8:8f79' in str(db_config.get('HOST', '')):
            print("  🚨 IPv6 ADDRESS FOUND IN DJANGO HOST CONFIG! ^^^")
            
    except Exception as e:
        print(f"  ❌ Error loading Django config: {e}")
    
    # 5. Check all environment variables for the IPv6 address
    print("\n🔍 SCANNING ALL ENVIRONMENT VARIABLES FOR IPv6:")
    found_vars = []
    for var, value in os.environ.items():
        if 'bea8:8f79' in str(value):
            found_vars.append(var)
    
    if found_vars:
        print("  🚨 IPv6 ADDRESS FOUND IN THESE VARIABLES:")
        for var in found_vars:
            print(f"    - {var}")
    else:
        print("  ✅ IPv6 address not found in environment variables")
        print("  💡 This means it might be:")
        print("     - Set dynamically by Railway")
        print("     - Coming from a service connection")
        print("     - Set in Railway dashboard but not visible in runtime")

if __name__ == '__main__':
    analyze_database_source()