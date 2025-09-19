#!/usr/bin/env python3
"""
PostgreSQL database management utility for local development.
Manages PostgreSQL database operations and configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_postgresql_status():
    """Check PostgreSQL service status."""
    print("🔍 Checking PostgreSQL status...")
    
    # Check if PostgreSQL service is running
    try:
        result = subprocess.run(["pg_isready"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL is running and accepting connections")
            return True
        else:
            print("❌ PostgreSQL is not running")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL command not found. Make sure PostgreSQL is installed and in PATH")
        return False

def show_database_info():
    """Show current database configuration."""
    print("🔍 Current database configuration:")
    
    local_settings_path = Path("main/local_settings.py")
    if not local_settings_path.exists():
        print("❌ local_settings.py not found")
        return
    
    with open(local_settings_path, 'r') as f:
        content = f.read()
    
    if "django.db.backends.postgresql" in content:
        print("📊 Using: PostgreSQL")
        print("   Database: tux_local")
        print("   Host: localhost:5432")
        print("   Engine: django.db.backends.postgresql")
    else:
        print("❌ PostgreSQL configuration not found in local_settings.py")
        return False
    
    # Check if database exists
    try:
        result = subprocess.run([
            "psql", "-U", "postgres", "-lqt", "|", "cut", "-d", "|", "-f", "1", "|", "grep", "-qw", "tux_local"
        ], shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database 'tux_local' exists")
        else:
            print("⚠️  Database 'tux_local' may not exist")
    except:
        print("⚠️  Could not verify database existence")

def create_database():
    """Create the local development database."""
    print("🔄 Creating local development database...")
    
    # Check if database already exists
    try:
        result = subprocess.run([
            "psql", "-U", "postgres", "-c", "SELECT 1 FROM pg_database WHERE datname='tux_local';"
        ], capture_output=True, text=True)
        
        if "1" in result.stdout:
            print("ℹ️  Database 'tux_local' already exists")
            return True
    except:
        pass
    
    # Create database
    try:
        result = subprocess.run([
            "psql", "-U", "postgres", "-c", "CREATE DATABASE tux_local;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database 'tux_local' created successfully")
            return True
        else:
            print(f"❌ Failed to create database: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def drop_database():
    """Drop the local development database."""
    print("🔄 Dropping local development database...")
    
    try:
        result = subprocess.run([
            "psql", "-U", "postgres", "-c", "DROP DATABASE IF EXISTS tux_local;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database 'tux_local' dropped successfully")
            return True
        else:
            print(f"❌ Failed to drop database: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error dropping database: {e}")
        return False

def reset_database():
    """Reset the local development database (drop and recreate)."""
    print("🔄 Resetting local development database...")
    
    if drop_database():
        if create_database():
            print("✅ Database reset successfully")
            print("🔄 Running migrations...")
            
            # Run migrations
            try:
                result = subprocess.run(["python", "manage.py", "migrate"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Migrations completed successfully")
                    return True
                else:
                    print(f"❌ Migrations failed: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ Error running migrations: {e}")
                return False
        else:
            return False
    else:
        return False

def run_migrations():
    """Run Django migrations."""
    print("🔄 Running Django migrations...")
    
    try:
        result = subprocess.run(["python", "manage.py", "migrate"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Migrations completed successfully")
            return True
        else:
            print(f"❌ Migrations failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python switch_database.py [status|create|drop|reset|migrate]")
        print("\nCommands:")
        print("  status   - Show current database status and configuration")
        print("  create   - Create the tux_local database")
        print("  drop     - Drop the tux_local database")
        print("  reset    - Drop and recreate the database with migrations")
        print("  migrate  - Run Django migrations")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_database_info()
        check_postgresql_status()
    elif command == "create":
        if check_postgresql_status():
            create_database()
    elif command == "drop":
        if check_postgresql_status():
            drop_database()
    elif command == "reset":
        if check_postgresql_status():
            reset_database()
    elif command == "migrate":
        if check_postgresql_status():
            run_migrations()
    else:
        print(f"❌ Unknown command: {command}")
        print("Use: status, create, drop, reset, or migrate")
        sys.exit(1)

if __name__ == "__main__":
    main()