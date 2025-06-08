from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin


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
