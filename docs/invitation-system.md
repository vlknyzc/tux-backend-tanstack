# Invitation-Based User Creation System

## Overview

The invitation system provides a secure way to create new user accounts through invitation links sent by existing authorized users. This system ensures that only invited users can register, providing better control over user onboarding.

## Core Components

### 1. Models

#### Invitation Model (`users/models.py`)

```python
class Invitation(models.Model):
    # Core fields
    token = UUIDField(unique=True, db_index=True)
    email = EmailField(db_index=True)

    # Metadata
    invitor = ForeignKey(UserAccount)
    workspace = ForeignKey(Workspace, null=True, blank=True)
    role = CharField(choices=ROLE_CHOICES, default='user')

    # Status tracking
    status = CharField(choices=STATUS_CHOICES, default='pending')
    expires_at = DateTimeField()
    used_at = DateTimeField(null=True, blank=True)
    used_by = ForeignKey(UserAccount, null=True, blank=True)
```

**Key Features:**

- UUID-based tokens for security (128+ bits entropy)
- Automatic expiration (default: 7 days)
- Status tracking (pending, used, expired, revoked)
- Audit trail with invitor and usage tracking
- Workspace-specific invitations with role assignment

### 2. API Endpoints

All endpoints follow the versioning pattern `/api/v1/` as per project standards [[memory:27837]].

#### Create Invitation

- **Endpoint:** `POST /api/v1/invitations/`
- **Authentication:** Required
- **Input:** email, workspace (optional), role, expires_at (optional)
- **Output:** Invitation details with unique token
- **Validation:**
  - Email uniqueness check
  - Duplicate invitation prevention per workspace
  - Role validation

#### Validate Invitation

- **Endpoint:** `GET /api/v1/invitations/{token}/validate/`
- **Authentication:** None required
- **Output:** Validation status, expiration info, invitor details
- **Features:** Non-destructive validation, automatic expiration status updates

#### Register via Invitation

- **Endpoint:** `POST /api/v1/register-via-invitation/`
- **Authentication:** None required
- **Input:** token, first_name, last_name, password, password_confirm
- **Process:**
  1. Validate invitation token
  2. Create user account
  3. Mark invitation as used
  4. Create workspace relationship (if applicable)
- **Validation:** Password strength, token validity, email availability

#### List Invitations

- **Endpoint:** `GET /api/v1/invitations/`
- **Authentication:** Required
- **Permissions:** Users see own invitations, superusers see all
- **Filters:** status, workspace
- **Output:** Paginated list with invitation details

#### Revoke Invitation

- **Endpoint:** `DELETE /api/v1/invitations/{id}/`
- **Authentication:** Required
- **Permissions:** Invitor or superuser can revoke
- **Action:** Marks invitation as revoked (soft delete)

#### Resend Invitation

- **Endpoint:** `POST /api/v1/invitations/{id}/resend/`
- **Authentication:** Required
- **Action:** Extends expiration by 7 days, resets status to pending

#### Invitation Statistics

- **Endpoint:** `GET /api/v1/invitations/stats/`
- **Authentication:** Required (Admin only)
- **Output:** Usage statistics, success rates, pending counts

### 3. Serializers

#### InvitationCreateSerializer

- Handles invitation creation
- Validates email uniqueness and duplicate invitations
- Auto-sets invitor from request context

#### RegisterViaInvitationSerializer

- Manages user registration via invitation
- Validates token, passwords, and creates user atomically
- Handles workspace relationship creation

#### InvitationValidationSerializer

- Provides detailed validation responses
- Includes expiration info and invitor details

### 4. Security Features

#### Token Security

- UUID4 tokens (128-bit entropy)
- Single-use only
- Automatic expiration
- Secure token generation

#### Validation & Authentication

- Email validation before invitation creation
- Password strength requirements (min 8 characters)
- Duplicate registration prevention
- CSRF protection on registration endpoint

#### Audit & Logging

- Complete audit trail of all invitation activities
- Invitor tracking
- Usage timestamps
- Status change history

#### Rate Limiting Considerations

- Invitation creation should be rate-limited per user
- Registration attempts should be rate-limited per IP
- Email sending should be rate-limited globally

### 5. Database Schema

```sql
CREATE TABLE users_invitation (
    id BIGSERIAL PRIMARY KEY,
    token UUID UNIQUE NOT NULL,
    email VARCHAR(254) NOT NULL,
    invitor_id BIGINT NOT NULL REFERENCES users_useraccount(id),
    workspace_id BIGINT REFERENCES master_data_workspace(id),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    used_by_id BIGINT REFERENCES users_useraccount(id)
);

-- Indexes for performance
CREATE INDEX users_invitation_token_idx ON users_invitation(token);
CREATE INDEX users_invitation_email_idx ON users_invitation(email);
CREATE INDEX users_invitation_email_status_idx ON users_invitation(email, status);
CREATE INDEX users_invitation_invitor_status_idx ON users_invitation(invitor_id, status);
CREATE INDEX users_invitation_expires_status_idx ON users_invitation(expires_at, status);
```

### 6. Admin Interface

The Django admin interface provides comprehensive invitation management:

#### Features

- List view with status indicators
- Filtering by status, role, workspace, invitor
- Search by email, invitor details, workspace name
- Bulk actions: revoke, extend expiration, mark expired
- Detailed view with all invitation information
- Visual status indicators (valid, expired, used, revoked)

#### Actions

- **Revoke:** Mark pending invitations as revoked
- **Extend Expiration:** Add 7 days to expiration date
- **Mark Expired:** Manually expire pending invitations

### 7. Error Handling

#### Common Error Responses

**400 Bad Request:**

- Invalid invitation token
- Expired invitation
- Already used invitation
- Password mismatch
- User already exists

**401 Unauthorized:**

- Missing authentication for protected endpoints

**403 Forbidden:**

- Insufficient permissions for admin endpoints
- Cannot revoke others' invitations (non-admin)

**404 Not Found:**

- Invitation token not found

**409 Conflict:**

- Duplicate invitation for same email/workspace

### 8. Configuration Options

#### Model Defaults

- Default expiration: 7 days
- Default role: 'user'
- Token generation: UUID4

#### Recommended Settings

- Maximum invitation lifetime: 30 days
- Maximum pending invitations per invitor: 10
- Rate limiting: 5 invitations per hour per user
- Password requirements: Django's built-in validators

### 9. Integration Points

#### Email Service Integration

The system is designed to integrate with email services for sending invitation links:

```python
# Future implementation
def send_invitation_email(invitation):
    invitation_url = invitation.get_invitation_url(settings.FRONTEND_URL)
    send_email(
        to=invitation.email,
        template='invitation_email',
        context={
            'invitation': invitation,
            'invitation_url': invitation_url,
            'invitor': invitation.invitor,
            'workspace': invitation.workspace
        }
    )
```

#### Frontend Integration

Frontend applications should:

1. Provide invitation creation forms for authorized users
2. Handle invitation validation on registration pages
3. Display invitation status and management interfaces
4. Implement proper error handling for all scenarios

### 10. Testing

#### Model Tests

- Invitation creation and validation
- Status transitions
- Expiration handling
- Relationship integrity

#### API Tests

- All endpoint functionality
- Authentication and permissions
- Error scenarios
- Edge cases (expired tokens, duplicate emails, etc.)

#### Integration Tests

- Complete invitation flow
- Email integration (when implemented)
- Frontend integration scenarios

### 11. Monitoring & Analytics

#### Key Metrics to Track

- Invitation creation rate
- Invitation usage rate (conversion)
- Time from invitation to registration
- Expiration rates
- Revocation rates

#### Recommended Dashboards

- Daily invitation statistics
- Conversion funnel analysis
- User onboarding metrics
- Workspace growth tracking

### 12. Future Enhancements

#### Planned Features

1. **Email Templates:** Rich HTML email templates for invitations
2. **Bulk Invitations:** CSV upload for multiple invitations
3. **Custom Expiration:** Per-invitation expiration settings
4. **Invitation Reminders:** Automated reminder emails
5. **Role-based Permissions:** Fine-grained invitation permissions
6. **Invitation Analytics:** Detailed reporting and analytics
7. **API Rate Limiting:** Built-in rate limiting middleware
8. **Webhook Support:** Integration webhooks for external systems

#### Security Enhancements

1. **IP Whitelisting:** Restrict invitation usage by IP
2. **Domain Restrictions:** Limit invitations to specific email domains
3. **Two-factor Setup:** Require 2FA setup during invitation registration
4. **Invitation Approval:** Admin approval workflow for invitations

## Implementation Status

✅ **Completed:**

- Core Invitation model with all required fields
- Complete API endpoint set with proper versioning
- Comprehensive serializers with validation
- Django admin interface with management actions
- Database migrations and indexes
- Security features (UUID tokens, expiration, audit trail)
- Permission system integration
- Error handling and validation

🔄 **Next Steps:**

- Email service integration
- Frontend integration testing
- Rate limiting implementation
- Comprehensive test suite
- Performance optimization
- Documentation updates

The invitation system is now fully functional and ready for integration with email services and frontend applications.
