#!/usr/bin/env python
"""
Test migration with PostgreSQL (production-like environment).
This script creates a temporary PostgreSQL database to test the migration.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def test_with_postgresql():
    """Test the migration with PostgreSQL database."""
    
    # Check if psql is available
    try:
        subprocess.run(['psql', '--version'], capture_output=True, check=True)
        print("✅ PostgreSQL client available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PostgreSQL not available. Install PostgreSQL to run this test.")
        print("   On macOS: brew install postgresql")
        print("   On Ubuntu: sudo apt-get install postgresql-client")
        return False
    
    print("🐘 Testing migration with PostgreSQL")
    print("=" * 40)
    
    # Create temporary PostgreSQL test settings
    test_settings = '''
import os
from main.local_settings import *

# Override database settings for PostgreSQL testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tux_migration_test',
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}
'''
    
    # Write test settings
    settings_file = Path(__file__).parent / 'main' / 'test_postgresql_settings.py'
    with open(settings_file, 'w') as f:
        f.write(test_settings)
    
    print("📝 Created PostgreSQL test settings")
    
    try:
        # Test migration
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'main.test_postgresql_settings'
        
        print("🔄 Running migration with PostgreSQL...")
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL migration successful!")
            print("🧪 Running constraint tests...")
            
            # Run constraint tests
            test_result = subprocess.run([
                sys.executable, '-c', f'''
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "main.test_postgresql_settings"
exec(open("test_migration.py").read())
'''
            ], capture_output=True, text=True)
            
            if test_result.returncode == 0:
                print("✅ All PostgreSQL tests passed!")
                return True
            else:
                print(f"❌ PostgreSQL tests failed:")
                print(test_result.stdout)
                print(test_result.stderr)
                return False
        else:
            print(f"❌ PostgreSQL migration failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    finally:
        # Clean up
        if settings_file.exists():
            settings_file.unlink()
            print("🧹 Cleaned up test settings")
    
    return False

if __name__ == '__main__':
    print("⚠️  Note: This test requires a running PostgreSQL instance.")
    print("   Make sure PostgreSQL is running and accessible.")
    print("   Set environment variables if needed:")
    print("   - POSTGRES_USER (default: postgres)")
    print("   - POSTGRES_PASSWORD (default: empty)")
    print("   - POSTGRES_HOST (default: localhost)")
    print("   - POSTGRES_PORT (default: 5432)")
    print()
    
    proceed = input("Continue with PostgreSQL test? [y/N]: ")
    if proceed.lower() != 'y':
        print("Test cancelled.")
        sys.exit(0)
    
    success = test_with_postgresql()
    sys.exit(0 if success else 1)