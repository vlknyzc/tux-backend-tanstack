#!/bin/bash
# Production deployment script for clean database setup

set -e  # Exit on any error

echo "🚀 Starting clean production database deployment..."

# Configuration - UPDATE THESE VALUES
DB_NAME="your_production_db_name"
DB_USER="your_db_user"
DB_HOST="your_db_host"
BACKUP_DIR="./backups"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Step 1: Backup current database
echo "📦 Creating database backup..."
BACKUP_FILE="$BACKUP_DIR/production_backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > $BACKUP_FILE
echo "✅ Backup created: $BACKUP_FILE"

# Step 2: Reset database tables
echo "🗑️  Dropping existing tables..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f scripts/reset_production_tables.sql
echo "✅ Tables dropped successfully"

# Step 3: Run migrations
echo "🔧 Running migrations..."
python manage.py migrate
echo "✅ Migrations completed"

# Step 4: Create superuser (optional)
echo "👤 Creating superuser..."
echo "Please create a superuser account:"
python manage.py createsuperuser

# Step 5: Collect static files (if needed)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "🎉 Clean deployment completed successfully!"
echo "📋 Summary:"
echo "   - Database backup: $BACKUP_FILE"
echo "   - All tables recreated with clean migrations"
echo "   - Ready for production use"
