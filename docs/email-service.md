# TUX Backend - Email Service Documentation

## Overview

The TUX Backend application now includes a comprehensive email service powered by Amazon SES (Simple Email Service) using boto3. This service provides reliable email delivery for user invitations, notifications, and system communications.

## Features

- ✅ **Amazon SES Integration**: Full integration with AWS SES using boto3
- ✅ **Template Support**: HTML and plain text email templates using Django's template system
- ✅ **Test Email Functionality**: Built-in test email capabilities
- ✅ **Quota Management**: SES quota monitoring and statistics
- ✅ **Email Verification**: SES email address verification
- ✅ **REST API Endpoints**: Complete API for email operations
- ✅ **Management Commands**: Django management commands for testing
- ✅ **Error Handling**: Comprehensive error handling and logging

## Configuration

### Environment Variables

The email service requires the following environment variables in your `.env.local` file:

```bash
# AWS SES Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SES_REGION_NAME=us-east-1
AWS_SES_REGION_ENDPOINT=email.us-east-1.amazonaws.com
AWS_SES_FROM_EMAIL=donotreply@yourdomain.com
```

### Django Settings

The following settings are already configured in `local_settings.py`:

```python
# Email settings
EMAIL_BACKEND = 'django_ses.SESBackend'
DEFAULT_FROM_EMAIL = getenv("AWS_SES_FROM_EMAIL")

AWS_ACCESS_KEY_ID = getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")
AWS_SES_REGION_NAME = getenv("AWS_SES_REGION_NAME")
AWS_SES_REGION_ENDPOINT = getenv("AWS_SES_REGION_ENDPOINT")
AWS_SES_FROM_EMAIL = getenv("AWS_SES_FROM_EMAIL")
USE_SES_V2 = True
```

## Email Service Components

### 1. Core Service (`users/services.py`)

The `SESEmailService` class provides the main email functionality:

```python
from users.services import email_service

# Send a simple test email
result = email_service.send_test_email("user@example.com")

# Send a template-based email
result = email_service.send_template_email(
    to_emails=["user@example.com"],
    subject="Welcome!",
    template_name="welcome",
    context={"user_name": "John"}
)

# Send a custom email
result = email_service.send_email(
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

# Check SES quota and send test email
python manage.py test_email user@example.com --template --check-quota

# Verify email address with SES
python manage.py test_email user@example.com --verify
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

#### Get SES Quota

```http
GET /api/v1/users/email/quota/
Authorization: JWT your_token_here
```

#### Verify Email Address

```http
POST /api/v1/users/email/verify/
Content-Type: application/json
Authorization: JWT your_token_here

{
    "email": "test@example.com"
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
from users.services import email_service

context = {
    'user_name': 'John Doe',
    'action_url': 'https://app.example.com/action',
    'expires_at': timezone.now() + timedelta(days=7)
}

result = email_service.send_template_email(
    to_emails=['john@example.com'],
    subject='Action Required',
    template_name='action_required',
    context=context
)
```

### 3. Bulk Email Sending

```python
from users.services import email_service

recipients = ['user1@example.com', 'user2@example.com']

for email in recipients:
    result = email_service.send_test_email(email)
    if result['success']:
        print(f"✅ Sent to {email}")
    else:
        print(f"❌ Failed to send to {email}: {result['message']}")
```

## Testing

### 1. Successful Test Results

The email service has been successfully tested:

```
Testing SES email service with vlknyzc@gmail.com

📊 Checking SES quota and statistics...
✅ Quota information retrieved:
   Max 24-hour send: 200.0
   Max send rate: 1.0
   Sent last 24 hours: 2.0

📤 Sending test email to vlknyzc@gmail.com...
✅ Email sent successfully
   Message ID: 010b0198e3c712d2-3bad902a-fc96-469b-b7eb-e2da7de59216-000000
   Recipient: vlknyzc@gmail.com
   From: donotreply@tuxonomy.com
```

### 2. Test Email Content

The test email includes:

- Professional HTML design with TUX Backend branding
- Configuration details table
- Success indicators
- Plain text fallback
- Responsive design

## Error Handling

The service includes comprehensive error handling:

- **AWS Credential Issues**: Clear error messages for missing/invalid credentials
- **SES Service Errors**: Detailed error codes and messages from AWS
- **Template Errors**: Graceful handling of missing templates
- **Network Issues**: Timeout and connection error handling
- **Validation Errors**: Input validation for email addresses and content

## Security Considerations

- ✅ Admin-only access to email endpoints
- ✅ Input validation and sanitization
- ✅ Rate limiting considerations (via SES quotas)
- ✅ Secure credential management via environment variables
- ✅ No sensitive data in logs

## SES Configuration Notes

### Sandbox Mode

If your SES account is in sandbox mode:

- You can only send emails to verified email addresses
- Maximum of 200 emails per 24-hour period
- Maximum send rate of 1 email per second

### Production Setup

For production use:

1. Request production access from AWS SES
2. Verify your domain (not just email addresses)
3. Set up proper SPF, DKIM, and DMARC records
4. Monitor bounce and complaint rates

## Dependencies

```
boto3==1.40.17
django-ses==4.4.0
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

The email service is now **fully integrated** with the invitation system. When a new invitation is created, an email is automatically sent to the recipient.

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

#### Testing Invitation Emails

```bash
# Test complete invitation flow
python manage.py test_invitation_email your-email@example.com --create-workspace --workspace-name "My Test Workspace"

# Test with specific invitor
python manage.py test_invitation_email your-email@example.com --invitor-email admin@example.com

# Create invitation without sending (template testing)
python manage.py test_invitation_email your-email@example.com --no-send
```

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

#### Successful Test Results

```
✅ Created test invitation:
   Token: a0470164-d219-4733-9181-239e225f85e7
   Email: vlknyzc@gmail.com
   Invitor: test.admin@tuxonomy.com
   Workspace: TUX Test Workspace
   Role: User

✅ Email sent successfully
   Message ID: 010b0198e3dd04ef-d01a326f-7725-406b-85aa-31d6fcc6e3db-000000
   Subject: You're invited to join TUX Test Workspace
```

## Next Steps

1. ✅ **Integration with Invitation System**: **COMPLETED** - Fully integrated with automatic email sending
2. **Additional Templates**: Create templates for password resets, welcome emails, etc.
3. **Email Analytics**: Consider adding email open/click tracking
4. **Background Processing**: For high-volume sending, consider using Celery for background processing
5. **Email Preferences**: Allow users to customize email notification preferences

## Support

For issues or questions about the email service:

1. Check the Django logs for error details
2. Verify AWS SES configuration and quotas
3. Test with the management command first
4. Ensure proper authentication for API endpoints

---

**Status**: ✅ **Fully Implemented and Tested**  
**Last Updated**: January 2025  
**Test Email Sent To**: vlknyzc@gmail.com (Successful)
