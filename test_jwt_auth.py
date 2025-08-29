#!/usr/bin/env python3
"""
Test JWT authentication to identify the 500 error cause.
"""

import os
import sys
import django
import json
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).resolve().parent))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.production_settings')

def test_jwt_authentication():
    """Test JWT authentication setup."""
    print("🔐 JWT AUTHENTICATION TEST")
    print("=" * 50)
    
    try:
        # Setup Django
        django.setup()
        
        # Test imports
        print("📦 Testing imports...")
        from rest_framework_simplejwt.views import TokenObtainPairView
        from users.views import CustomTokenObtainPairView
        from users.models import UserAccount
        from django.contrib.auth import authenticate
        print("✅ All imports successful")
        
        # Check JWT configuration
        print("\n⚙️ JWT Configuration:")
        from django.conf import settings
        jwt_config = settings.SIMPLE_JWT
        print(f"  ACCESS_TOKEN_LIFETIME: {jwt_config.get('ACCESS_TOKEN_LIFETIME')}")
        print(f"  REFRESH_TOKEN_LIFETIME: {jwt_config.get('REFRESH_TOKEN_LIFETIME')}")
        print(f"  ALGORITHM: {jwt_config.get('ALGORITHM')}")
        print(f"  AUTH_HEADER_TYPES: {jwt_config.get('AUTH_HEADER_TYPES')}")
        
        # Check if SECRET_KEY is available
        secret_key = getattr(settings, 'SECRET_KEY', None)
        if secret_key:
            print(f"  SECRET_KEY: {'*' * 8} (length: {len(secret_key)})")
        else:
            print("  ❌ SECRET_KEY: NOT SET")
            return False
        
        # Check user model
        print(f"\n👤 User Model: {settings.AUTH_USER_MODEL}")
        
        # Test creating a test user (won't actually create, just test the process)
        print("\n🧪 Testing User Creation Process...")
        try:
            # Check if we can access UserAccount manager
            manager = UserAccount.objects
            print("✅ UserAccount manager accessible")
            
            # Check if we can query users
            user_count = UserAccount.objects.count()
            print(f"✅ Current user count: {user_count}")
            
            if user_count > 0:
                # Get a sample user to test authentication
                sample_user = UserAccount.objects.first()
                print(f"✅ Sample user found: {sample_user.email}")
                
                # Test authentication method exists
                if hasattr(sample_user, 'check_password'):
                    print("✅ User has check_password method")
                else:
                    print("❌ User missing check_password method")
                    
        except Exception as e:
            print(f"❌ User model test failed: {e}")
            return False
        
        # Test JWT token generation
        print("\n🎫 Testing JWT Token Generation...")
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            
            if user_count > 0:
                sample_user = UserAccount.objects.first()
                
                # Try to generate tokens
                refresh = RefreshToken.for_user(sample_user)
                access = refresh.access_token
                
                print("✅ JWT token generation successful")
                print(f"  Refresh token (first 20 chars): {str(refresh)[:20]}...")
                print(f"  Access token (first 20 chars): {str(access)[:20]}...")
            else:
                print("⚠️ No users available for token generation test")
                
        except Exception as e:
            print(f"❌ JWT token generation failed: {e}")
            return False
        
        # Test the view class
        print("\n🎯 Testing CustomTokenObtainPairView...")
        try:
            view = CustomTokenObtainPairView()
            print("✅ CustomTokenObtainPairView instantiated successfully")
            
            # Check if it has the required methods
            if hasattr(view, 'post'):
                print("✅ View has post method")
            else:
                print("❌ View missing post method")
                
        except Exception as e:
            print(f"❌ CustomTokenObtainPairView test failed: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 ALL JWT AUTHENTICATION TESTS PASSED!")
        print("💡 The 500 error might be due to:")
        print("   - Missing or invalid user credentials in the request")
        print("   - Database connection issues during authentication")
        print("   - CORS or middleware configuration issues")
        print("   - Cookie/session configuration problems")
        
        return True
        
    except Exception as e:
        print(f"💥 JWT authentication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_common_jwt_issues():
    """Check for common JWT authentication issues."""
    print("\n🔍 COMMON JWT ISSUES CHECK")
    print("=" * 50)
    
    try:
        from django.conf import settings
        
        # Check AUTH_COOKIE settings
        cookie_settings = [
            'AUTH_COOKIE_ACCESS_MAX_AGE',
            'AUTH_COOKIE_REFRESH_MAX_AGE', 
            'AUTH_COOKIE_SECURE',
            'AUTH_COOKIE_HTTP_ONLY',
            'AUTH_COOKIE_PATH',
            'AUTH_COOKIE_SAMESITE'
        ]
        
        print("🍪 Cookie Configuration:")
        missing_settings = []
        for setting in cookie_settings:
            value = getattr(settings, setting, 'NOT SET')
            print(f"  {setting}: {value}")
            if value == 'NOT SET':
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"⚠️ Missing cookie settings: {missing_settings}")
        else:
            print("✅ All cookie settings present")
        
        # Check middleware
        print(f"\n🔧 Middleware Check:")
        middleware = settings.MIDDLEWARE
        cors_middleware = 'corsheaders.middleware.CorsMiddleware'
        auth_middleware = 'django.contrib.auth.middleware.AuthenticationMiddleware'
        
        if cors_middleware in middleware:
            print(f"✅ CORS middleware present")
        else:
            print(f"⚠️ CORS middleware missing")
            
        if auth_middleware in middleware:
            print(f"✅ Authentication middleware present")
        else:
            print(f"❌ Authentication middleware missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Common issues check failed: {e}")
        return False


def main():
    """Main test function."""
    print("🔐 JWT Authentication Diagnostic Tool")
    print("=" * 60)
    
    success1 = test_jwt_authentication()
    success2 = check_common_jwt_issues()
    
    if success1 and success2:
        print("\n🎉 JWT authentication setup appears correct!")
        print("💡 To debug the 500 error, check:")
        print("   1. Django logs for specific error details")
        print("   2. Network requests in browser dev tools")
        print("   3. Request payload format (should be JSON with email/password)")
        return 0
    else:
        print("\n💥 JWT authentication has configuration issues!")
        return 1


if __name__ == '__main__':
    sys.exit(main())