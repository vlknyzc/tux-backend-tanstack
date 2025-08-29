#!/usr/bin/env python3
"""
Emergency Django diagnostic script.
Tests Django setup without running the full server.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).resolve().parent))

def emergency_django_test():
    """Test Django setup step by step."""
    print("🚨 EMERGENCY DJANGO DIAGNOSTIC")
    print("=" * 50)
    
    try:
        # Step 1: Test environment variables
        print("1. 🔍 Environment Variables:")
        django_settings = os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')
        secret_key = os.environ.get('SECRET_KEY', 'NOT SET')
        
        print(f"   DJANGO_SETTINGS_MODULE: {django_settings}")
        print(f"   SECRET_KEY: {'SET' if secret_key != 'NOT SET' else 'NOT SET'}")
        
        if django_settings == 'NOT SET':
            print("   ⚠️ Setting DJANGO_SETTINGS_MODULE to main.production_settings")
            os.environ['DJANGO_SETTINGS_MODULE'] = 'main.production_settings'
        
        # Step 2: Test Django import
        print("\\n2. 📦 Django Import:")
        try:
            import django
            print(f"   ✅ Django imported successfully (version: {django.get_version()})")
        except Exception as e:
            print(f"   ❌ Django import failed: {e}")
            return False
        
        # Step 3: Test settings import
        print("\\n3. ⚙️ Settings Import:")
        try:
            from django.conf import settings
            print("   ✅ Settings imported")
        except Exception as e:
            print(f"   ❌ Settings import failed: {e}")
            return False
        
        # Step 4: Test Django setup
        print("\\n4. 🚀 Django Setup:")
        try:
            django.setup()
            print("   ✅ Django setup successful")
        except Exception as e:
            print(f"   ❌ Django setup failed: {e}")
            return False
        
        # Step 5: Test basic settings
        print("\\n5. 📋 Basic Settings Check:")
        try:
            print(f"   DEBUG: {getattr(settings, 'DEBUG', 'NOT SET')}")
            print(f"   SECRET_KEY: {'SET' if getattr(settings, 'SECRET_KEY', None) else 'NOT SET'}")
            print(f"   ALLOWED_HOSTS: {len(getattr(settings, 'ALLOWED_HOSTS', []))} hosts")
            print(f"   DATABASES: {'configured' if getattr(settings, 'DATABASES', None) else 'NOT SET'}")
        except Exception as e:
            print(f"   ❌ Settings check failed: {e}")
            return False
        
        # Step 6: Test apps import
        print("\\n6. 📱 Apps Import Test:")
        try:
            from users.models import UserAccount
            print("   ✅ users.models imported")
        except Exception as e:
            print(f"   ❌ users.models import failed: {e}")
            return False
        
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            print("   ✅ rest_framework_simplejwt imported")
        except Exception as e:
            print(f"   ❌ rest_framework_simplejwt import failed: {e}")
            return False
        
        # Step 7: Test database connection (basic)
        print("\\n7. 🗄️ Database Connection Test:")
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            print("   ✅ Database connection successful")
        except Exception as e:
            print(f"   ⚠️ Database connection failed: {e}")
            print("   (This may be expected if database is not ready)")
        
        # Step 8: Test URL configuration
        print("\\n8. 🌐 URL Configuration Test:")
        try:
            from django.urls import get_resolver
            resolver = get_resolver()
            print("   ✅ URL configuration loaded")
        except Exception as e:
            print(f"   ❌ URL configuration failed: {e}")
            return False
        
        print("\\n" + "=" * 50)
        print("🎉 DJANGO EMERGENCY TEST PASSED!")
        print("💡 Django setup appears to be working correctly")
        return True
        
    except Exception as e:
        print(f"\\n💥 EMERGENCY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = emergency_django_test()
    sys.exit(0 if success else 1)