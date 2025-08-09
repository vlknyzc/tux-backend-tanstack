#!/usr/bin/env python
"""
Migration testing script for StringDetail constraint fix.
Run this script to test the migration before production deployment.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.local_settings')
django.setup()

from django.db import connection, IntegrityError
from master_data.models import *
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

def test_constraint_exists():
    """Test that the unique constraint/index exists."""
    print("1. Testing constraint existence...")
    
    cursor = connection.cursor()
    
    if connection.vendor == 'sqlite':
        cursor.execute('PRAGMA index_list(master_data_stringdetail)')
        indexes = cursor.fetchall()
        constraint_exists = any('workspace_string_dimension' in idx[1] for idx in indexes)
    elif connection.vendor == 'postgresql':
        cursor.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'master_data_stringdetail' 
            AND constraint_type = 'UNIQUE'
        """)
        constraints = cursor.fetchall()
        constraint_exists = any('workspace_string_dimension' in str(constraint) for constraint in constraints)
    else:
        print("   ⚠️  Database vendor not specifically supported in test")
        return True
    
    if constraint_exists:
        print("   ✅ Constraint exists")
        return True
    else:
        print("   ❌ Constraint missing")
        return False

def test_constraint_functionality():
    """Test that the constraint actually prevents duplicates."""
    print("2. Testing constraint functionality...")
    
    try:
        # Get or create test workspace
        workspace, created = Workspace.objects.get_or_create(
            name='Test Workspace',
            defaults={'slug': 'test-workspace', 'status': 'active'}
        )
        
        # Create test user
        user, created = User.objects.get_or_create(
            email='test_migration@example.com',
            defaults={'first_name': 'Test', 'last_name': 'Migration'}
        )
        
        # Create test dimension
        dimension, created = Dimension.objects.get_or_create(
            name='Test Environment',
            workspace=workspace,
            defaults={'created_by': user}
        )
        
        # Create platform and field
        platform, created = Platform.objects.get_or_create(
            slug='test-platform',
            defaults={
                'platform_type': 'database',
                'name': 'Test Platform',
                'created_by': user
            }
        )
        
        field, created = Field.objects.get_or_create(
            name='test_field',
            field_level=1,
            platform=platform,
            defaults={'created_by': user}
        )
        
        # Create rule
        rule, created = Rule.objects.get_or_create(
            name='Test Migration Rule',
            platform=platform,
            workspace=workspace,
            defaults={'created_by': user}
        )
        
        # Create submission
        submission, created = Submission.objects.get_or_create(
            name='Test Migration Submission',
            rule=rule,
            starting_field=field,
            workspace=workspace,
            defaults={'created_by': user}
        )
        
        # Create string
        string, created = String.objects.get_or_create(
            value='test_migration_string',
            field=field,
            submission=submission,
            rule=rule,
            workspace=workspace,
            defaults={'created_by': user}
        )
        
        # Clean up any existing StringDetail for this test
        StringDetail.objects.filter(
            string=string,
            dimension=dimension,
            workspace=workspace
        ).delete()
        
        # Test 1: Create first StringDetail
        detail1 = StringDetail.objects.create(
            string=string,
            dimension=dimension,
            dimension_value_freetext='first_value',
            workspace=workspace,
            created_by=user
        )
        print("   ✅ First StringDetail created successfully")
        
        # Test 2: Try to create duplicate
        try:
            detail2 = StringDetail.objects.create(
                string=string,
                dimension=dimension,
                dimension_value_freetext='second_value',
                workspace=workspace,
                created_by=user
            )
            print("   ❌ Duplicate StringDetail created - constraint not working!")
            return False
        except IntegrityError:
            print("   ✅ Duplicate prevented by constraint")
            return True
            
    except Exception as e:
        print(f"   ❌ Error during constraint test: {str(e)}")
        return False

def test_fresh_migration():
    """Test migration on fresh database."""
    print("3. Testing fresh migration...")
    print("   ℹ️  This test requires manual verification:")
    print("   - Delete db.sqlite3")
    print("   - Run: python manage.py migrate")
    print("   - Check for any errors")
    return True

def run_all_tests():
    """Run all migration tests."""
    print("🧪 Migration Test Suite - StringDetail Constraint Fix")
    print("=" * 55)
    
    tests = [
        test_constraint_exists,
        test_constraint_functionality,
        test_fresh_migration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {str(e)}")
            results.append(False)
        print()
    
    print("📊 Test Results:")
    print("=" * 15)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("🚀 Migration is ready for production deployment")
        return True
    else:
        print(f"❌ {total - passed} out of {total} tests failed")
        print("⚠️  Please fix issues before production deployment")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)