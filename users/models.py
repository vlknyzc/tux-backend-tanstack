from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import uuid


class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        email = email.lower()

        user = self.model(
            email=email,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(
            email,
            password=password,
            **kwargs
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Workspace relationships
    workspaces = models.ManyToManyField(
        'master_data.Workspace',
        through='WorkspaceUser',
        related_name='users',
        blank=True,
        help_text="Workspaces this user has access to"
    )

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    def has_workspace_access(self, workspace_id):
        """Check if user has access to a specific workspace"""
        if self.is_superuser:
            return True
        return self.workspaces.filter(id=workspace_id).exists()

    def get_accessible_workspaces(self):
        """Get all workspaces the user can access"""
        if self.is_superuser:
            from master_data.models import Workspace
            return Workspace.objects.all()
        return self.workspaces.filter(workspaceuser__is_active=True)

    def get_workspace_role(self, workspace_id):
        """Get user's role in a specific workspace"""
        if self.is_superuser:
            return 'superuser'
        try:
            workspace_user = self.workspaceuser_set.get(
                workspace_id=workspace_id, is_active=True)
            return workspace_user.role
        except WorkspaceUser.DoesNotExist:
            return None


class WorkspaceUser(models.Model):
    """
    Through model for User-Workspace relationship with roles
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
    ]

    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    workspace = models.ForeignKey(
        'master_data.Workspace', on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text="User's role in this workspace"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this workspace assignment is active"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'workspace')]
        verbose_name = "Workspace User"
        verbose_name_plural = "Workspace Users"

    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"


class Invitation(models.Model):
    """
    Model for user invitations with secure token-based registration
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    ROLE_CHOICES = WorkspaceUser.ROLE_CHOICES  # Reuse role choices from WorkspaceUser

    # Core fields
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique invitation token"
    )
    email = models.EmailField(
        db_index=True,
        help_text="Email address of the invited user"
    )
    
    # Invitation metadata
    invitor = models.ForeignKey(
        'UserAccount',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
        help_text="User who sent this invitation"
    )
    workspace = models.ForeignKey(
        'master_data.Workspace',
        on_delete=models.CASCADE,
        related_name='invitations',
        help_text="Workspace the user is being invited to",
        null=True,
        blank=True
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text="Role to assign to the invited user"
    )
    
    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the invitation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text="When this invitation expires"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this invitation was used"
    )
    
    # User who used the invitation (if any)
    used_by = models.ForeignKey(
        'UserAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_invitations',
        help_text="User who used this invitation"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['invitor', 'status']),
            models.Index(fields=['expires_at', 'status']),
        ]

    def save(self, *args, **kwargs):
        """Set default expiration if not provided"""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invitation for {self.email} by {self.invitor.email} ({self.status})"

    @property
    def is_valid(self):
        """Check if invitation is valid for use"""
        return (
            self.status == 'pending' and
            timezone.now() < self.expires_at
        )

    @property
    def is_expired(self):
        """Check if invitation has expired"""
        return timezone.now() >= self.expires_at

    def mark_as_used(self, user):
        """Mark invitation as used by a user"""
        self.status = 'used'
        self.used_at = timezone.now()
        self.used_by = user
        self.save(update_fields=['status', 'used_at', 'used_by', 'updated_at'])

    def mark_as_revoked(self):
        """Mark invitation as revoked"""
        self.status = 'revoked'
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_expired(self):
        """Mark invitation as expired"""
        self.status = 'expired'
        self.save(update_fields=['status', 'updated_at'])

    def get_invitation_url(self, base_url):
        """Generate the invitation URL"""
        return f"{base_url}/register?token={self.token}"
