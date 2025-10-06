# tuxonomy.com - Email Service Documentation

## Overview

The tuxonomy.com application uses **Resend** for sending emails. This service provides reliable email delivery for user invitations, notifications, and system communications.

## Features

- ✅ **Resend Integration**: Full integration with Resend API
- ✅ **Template Support**: HTML and plain text email templates using Django's template system
- ✅ **Test Email Functionality**: Built-in test email capabilities
- ✅ **REST API Endpoints**: Complete API for email operations
- ✅ **Management Commands**: Django management commands for testing
- ✅ **Error Handling**: Comprehensive error handling and logging

## Configuration

### Environment Variables

The email service requires the following environment variables in your `.env.local` file:

```bash
# Resend Configuration
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=noreply@yourdomain.com
```

### Getting Your Resend API Key

1. Sign up at [resend.com](https://resend.com)
2. Verify your domain
3. Generate an API key from the dashboard
4. Add the API key to your `.env.local` file

### Django Settings

The following settings are configured in `local_settings.py` and `production_settings.py`:

**Local (Development):**

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Prints to console
DEFAULT_FROM_EMAIL = getenv("FROM_EMAIL", "noreply@tuxonomy.com")
RESEND_API_KEY = getenv("RESEND_API_KEY")
```

**Production:**

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
DEFAULT_FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@tuxonomy.com")
```

## Email Service Components

### 1. Core Service (`users/services.py`)

The `ResendEmailService` class provides the main email functionality:

```python
from users.services import get_email_service

# Send a simple test email
result = get_email_service().send_test_email("user@example.com")

# Send a template-based email
result = get_email_service().send_template_email(
    to_emails=["user@example.com"],
    subject="Welcome!",
    template_name="welcome",
    context={"user_name": "John"}
)

# Send a custom email
result = get_email_service().send_email(
    to_emails=["user@example.com"],
    subject="Custom Subject",
    html_content="<h1>Hello!</h1>",
    text_content="Hello!"
)
```

### 2. Email Templates

Email templates are stored in `templates/emails/`:

- `test_email.html` / `test_email.txt` - Test email templates
- `invitation.html` / `invitation.txt` - User invitation templates

#### Creating New Templates

1. Create HTML template: `templates/emails/your_template.html`
2. Create text template (optional): `templates/emails/your_template.txt`
3. Use Django template syntax with context variables

### 3. Management Commands

#### Send Test Email

```bash
# Basic test email
python manage.py test_email user@example.com

# Test email with template
python manage.py test_email user@example.com --template
```

### 4. REST API Endpoints

All email endpoints require authentication and admin permissions:

#### Send Test Email

```http
POST /api/v1/users/email/test/
Content-Type: application/json
Authorization: JWT your_token_here

{
    "email": "test@example.com",
    "use_template": true
}
```

#### Send Custom Email

```http
POST /api/v1/users/email/send/
Content-Type: application/json
Authorization: JWT your_token_here

{
    "to_emails": ["user@example.com"],
    "subject": "Custom Subject",
    "html_content": "<h1>HTML Content</h1>",
    "text_content": "Plain text content",
    "cc_emails": ["cc@example.com"],
    "bcc_emails": ["bcc@example.com"]
}
```

## Usage Examples

### 1. Sending Invitation Emails

```python
from users.services import send_invitation_email

# Send invitation email (automatically uses template)
invitation = Invitation.objects.get(token=some_token)
result = send_invitation_email(invitation)

if result['success']:
    print(f"Invitation sent! Message ID: {result['message_id']}")
else:
    print(f"Failed to send invitation: {result['message']}")
```

### 2. Custom Email with Template

```python
from users.services import get_email_service

context = {
    'user_name': 'John Doe',
    'action_url': 'https://app.example.com/action',
    'expires_at': timezone.now() + timedelta(days=7)
}

result = get_email_service().send_template_email(
    to_emails=['john@example.com'],
    subject='Action Required',
    template_name='action_required',
    context=context
)
```

### 3. Bulk Email Sending

```python
from users.services import get_email_service

recipients = ['user1@example.com', 'user2@example.com']

for email in recipients:
    result = get_email_service().send_test_email(email)
    if result['success']:
        print(f"✅ Sent to {email}")
    else:
        print(f"❌ Failed to send to {email}: {result['message']}")
```

## Error Handling

The service includes comprehensive error handling:

- **Missing API Key**: Clear error messages for missing/invalid API keys
- **Resend Service Errors**: Detailed error codes and messages from Resend
- **Template Errors**: Graceful handling of missing templates
- **Network Issues**: Timeout and connection error handling
- **Validation Errors**: Input validation for email addresses and content

## Security Considerations

- ✅ Admin-only access to email endpoints
- ✅ Input validation and sanitization
- ✅ Secure credential management via environment variables
- ✅ No sensitive data in logs

## Resend Configuration Notes

### Domain Verification

1. Add your domain to Resend
2. Add the required DNS records (SPF, DKIM, DMARC)
3. Wait for verification (usually takes a few minutes)
4. Start sending emails from your verified domain

### Rate Limits

Resend has different rate limits based on your plan:

- Free tier: 100 emails/day
- Paid plans: Higher limits based on subscription

Check the [Resend documentation](https://resend.com/docs) for current limits.

## Dependencies

```
resend==2.8.0
django>=4.2
```

## File Structure

```
users/
├── services.py              # Main email service
├── email_views.py          # REST API endpoints
├── management/
│   └── commands/
│       └── test_email.py   # Management command
└── urls.py                 # URL routing

templates/
└── emails/
    ├── test_email.html     # Test email HTML template
    ├── test_email.txt      # Test email text template
    ├── invitation.html     # Invitation HTML template
    └── invitation.txt      # Invitation text template
```

## Invitation Email Integration

### Automatic Email Sending

The email service is **fully integrated** with the invitation system. When a new invitation is created, an email is automatically sent to the recipient.

#### How It Works

1. **Django Signals**: A `post_save` signal on the `Invitation` model automatically triggers email sending
2. **Template-Based**: Uses professional HTML and plain text templates
3. **Error Handling**: Comprehensive logging and error handling for failed sends
4. **Status Tracking**: All email attempts are logged for audit purposes

#### Files Involved

- `users/signals.py` - Django signals for automatic email sending
- `users/apps.py` - Signal registration
- `templates/emails/invitation.html` - Professional HTML template
- `templates/emails/invitation.txt` - Plain text fallback
- `users/services.py` - Email service integration

#### Email Template Features

- 📱 **Responsive Design**: Works on all devices
- 🎨 **Professional Styling**: Modern, clean design with TUX branding
- 🔗 **Clear Call-to-Action**: Prominent registration button
- ⏰ **Expiry Notice**: Clear expiration date and urgency
- 📋 **Workspace Details**: Complete invitation context
- 🔒 **Security Notes**: Professional footer with security information

#### API Integration

When creating invitations via the REST API, emails are sent automatically:

```http
POST /api/v1/users/invitations/
Content-Type: application/json
Authorization: JWT your_token_here

{
    "email": "newuser@example.com",
    "workspace": 1,
    "role": "user"
}
```

The response includes invitation details, and the email is sent in the background.

## Migration from Amazon SES

This project was previously using Amazon SES. The migration to Resend includes:

1. ✅ Removed `boto3`, `botocore`, `django-ses`, and related AWS dependencies
2. ✅ Replaced `SESEmailService` with `ResendEmailService`
3. ✅ Updated all email configuration in settings files
4. ✅ Updated management commands and API views
5. ✅ Simplified email service with fewer dependencies

### Benefits of Resend

- **Simpler Setup**: No AWS account or complex IAM configuration needed
- **Better Developer Experience**: Clean API and excellent documentation
- **Modern Features**: Built for developers with great tooling
- **Easier Domain Verification**: Simpler DNS setup process
- **Better Pricing**: More predictable pricing model

## Support

For issues or questions about the email service:

1. Check the Django logs for error details
2. Verify Resend API key configuration
3. Check domain verification status in Resend dashboard
4. Test with the management command first
5. Ensure proper authentication for API endpoints

## Resources

- [Resend Documentation](https://resend.com/docs)
- [Resend Python SDK](https://github.com/resend/resend-python)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)

---

**Status**: ✅ **Migrated to Resend**
**Last Updated**: January 2025
**Email Provider**: Resend
