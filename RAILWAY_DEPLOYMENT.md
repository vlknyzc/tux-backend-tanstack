# Railway Deployment Guide

Complete guide for deploying and managing your Django application on Railway.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Creating Superuser](#creating-superuser)
3. [Environment Variables](#environment-variables)
4. [Post-Deployment Tasks](#post-deployment-tasks)
5. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### Prerequisites

- Railway account at https://railway.app
- Railway CLI installed: `npm i -g @railway/cli`
- Project deployed to Railway

### Deploy to Railway

```bash
# Login to Railway
railway login

# Link to your project
railway link

# Deploy
git push origin main  # or your deployment branch
```

---

## Creating Superuser

There are several methods to create a superuser on Railway:

### Method 1: Railway Dashboard Shell (Easiest) ⭐

1. Go to https://railway.app/dashboard
2. Select your project → Django service
3. Click **"..."** menu (three dots) → **"Shell"**
4. In the shell, run:
   ```bash
   python manage.py create_initial_superuser \
     --email admin@yourcompany.com \
     --password YourSecurePassword123! \
     --first-name Admin \
     --last-name User
   ```

### Method 2: Railway CLI Shell

```bash
# Open interactive shell on Railway
railway shell

# Then create superuser
python manage.py create_initial_superuser \
  --email admin@yourcompany.com \
  --password YourSecurePassword123! \
  --first-name Admin \
  --last-name User
```

### Method 3: Django's Interactive Command

```bash
# For interactive prompt
railway shell
python manage.py createsuperuser
# Follow the prompts
```

### Method 4: Automatic Creation via Environment Variables

Set these environment variables in Railway Dashboard:

| Variable               | Example Value       | Description                            |
| ---------------------- | ------------------- | -------------------------------------- |
| `CREATE_SUPERUSER`     | `true`              | Enable auto-creation on deployment     |
| `SUPERUSER_EMAIL`      | `admin@example.com` | Admin email address                    |
| `SUPERUSER_PASSWORD`   | `SecurePass123!`    | Initial password (change after login!) |
| `SUPERUSER_FIRST_NAME` | `Admin`             | First name                             |
| `SUPERUSER_LAST_NAME`  | `User`              | Last name                              |

Then redeploy or run:

```bash
railway shell
python manage.py create_initial_superuser --skip-existing
```

---

## Environment Variables

### Required Variables

Set these in Railway Dashboard → Your Service → Variables:

```bash
# Django Settings
DJANGO_ENV=PRODUCTION
SECRET_KEY=your-secret-key-here
DEBUG=False

# Database (automatically set by Railway PostgreSQL plugin)
PGHOST=<auto-set>
PGPORT=<auto-set>
PGDATABASE=<auto-set>
PGUSER=<auto-set>
PGPASSWORD=<auto-set>
DATABASE_URL=<auto-set>

# Security
ALLOWED_HOSTS=your-app.railway.app,your-custom-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://www.your-frontend.com

# Email (for invitations and notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourcompany.com
```

### Optional Variables

```bash
# Superuser Auto-Creation
CREATE_SUPERUSER=true
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=ChangeMe123!
SUPERUSER_FIRST_NAME=Admin
SUPERUSER_LAST_NAME=User

# Performance
GUNICORN_WORKERS=4
GUNICORN_THREADS=2

# Caching (if using Redis)
REDIS_URL=<redis-url>
CACHE_BACKEND=redis
```

---

## Post-Deployment Tasks

After your first deployment, complete these setup steps:

### 1. Create Superuser (if not auto-created)

```bash
railway shell
python manage.py create_initial_superuser --email admin@company.com --password SecurePass123!
```

### 2. Create Workspace

```bash
railway shell
python manage.py create_workspace "Your Company Name" --admin-email admin@company.com
```

### 3. Seed Platform Data (already done in deploy.py)

```bash
railway shell
python manage.py seed_platforms
```

### 4. Verify Setup

```bash
railway shell
python manage.py shell

# In Django shell:
from django.contrib.auth import get_user_model
from master_data.models import Workspace, Platform

print(f"Superusers: {get_user_model().objects.filter(is_superuser=True).count()}")
print(f"Workspaces: {Workspace.objects.count()}")
print(f"Platforms: {Platform.objects.count()}")
exit()
```

### 5. Access Your Application

- **Admin Panel**: `https://your-app.railway.app/admin/`
- **API Documentation**: `https://your-app.railway.app/api/schema/swagger-ui/`
- **Health Check**: `https://your-app.railway.app/health/`

---

## Managing Users and Workspaces

### Create New Workspace

```bash
railway shell
python manage.py create_workspace "Client Name" \
  --slug client-slug \
  --admin-email client-admin@example.com \
  --create-admin  # Creates user if doesn't exist
```

### Assign User to Workspace

```bash
railway shell
python manage.py assign_user_to_workspace \
  user@example.com \
  workspace-slug \
  --role admin  # or 'user' or 'viewer'
```

### List All Users

```bash
railway shell
python manage.py shell -c "
from django.contrib.auth import get_user_model
for u in get_user_model().objects.all():
    print(f'{u.email} - Superuser: {u.is_superuser}')
"
```

---

## Troubleshooting

### Cannot Connect to Database Locally

**Problem**: Running `railway run python manage.py ...` fails with connection error.

**Solution**: Use `railway shell` instead:

- ❌ Wrong: `railway run python manage.py createsuperuser`
- ✅ Correct: `railway shell` then `python manage.py createsuperuser`

**Why**: `railway run` runs commands locally with Railway's environment variables. Railway's internal database hostname (`postgres.railway.internal`) is only accessible from within Railway's network.

### Superuser Already Exists

If you get "Superuser already exists" error, list existing superusers:

```bash
railway shell
python manage.py shell -c "
from django.contrib.auth import get_user_model
for u in get_user_model().objects.filter(is_superuser=True):
    print(f'{u.email} - {u.get_full_name()}')
"
```

### Reset Superuser Password

```bash
railway shell
python manage.py shell

# In Django shell:
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='admin@example.com')
user.set_password('NewPassword123!')
user.save()
print('Password updated successfully!')
exit()
```

### View Deployment Logs

```bash
# Real-time logs
railway logs

# Follow logs
railway logs --follow
```

### Run Database Migrations Manually

```bash
railway shell
python manage.py migrate --verbosity=2
```

### Check Environment Variables

```bash
railway variables
```

### Connect to PostgreSQL Database

```bash
# Get database URL
railway variables | grep DATABASE_URL

# Connect using psql (if installed)
railway connect
```

---

## Useful Commands

### Check Application Health

```bash
curl https://your-app.railway.app/health/
```

### Run Django Shell

```bash
railway shell
python manage.py shell
```

### Create Database Backup

```bash
railway connect
# Then use pg_dump commands
```

### Update Environment Variable

```bash
railway variables set KEY=value
```

### Restart Service

```bash
railway up --detach
```

---

## Security Best Practices

1. **Change Default Passwords**: Immediately change any auto-generated passwords
2. **Use Strong Secrets**: Generate strong `SECRET_KEY` using https://djecrety.ir/
3. **Enable 2FA**: Enable two-factor authentication for Railway account
4. **Rotate Credentials**: Regularly rotate database passwords and API keys
5. **Monitor Logs**: Regularly check Railway logs for suspicious activity
6. **Limit Access**: Only give Railway project access to team members who need it

---

## Support

- Railway Documentation: https://docs.railway.app/
- Django Documentation: https://docs.djangoproject.com/
- Project Issues: [Your GitHub Issues]

---

## Quick Reference

```bash
# Essential Commands
railway login                    # Login to Railway
railway link                     # Link to project
railway shell                    # Interactive shell
railway logs                     # View logs
railway variables                # List env vars
railway connect                  # Connect to database

# Management Commands
python manage.py createsuperuser                    # Interactive superuser creation
python manage.py create_initial_superuser           # Non-interactive superuser
python manage.py create_workspace "Name"            # Create workspace
python manage.py assign_user_to_workspace           # Assign user
python manage.py seed_platforms                     # Seed platform data
python manage.py migrate                            # Run migrations
python manage.py collectstatic                      # Collect static files
```
