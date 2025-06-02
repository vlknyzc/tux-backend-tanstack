"""
Constants for master_data app.
Centralizes magic numbers, choices, and other constants for better maintainability.
"""

from django.db import models

# Field length constants
STANDARD_NAME_LENGTH = 30
SLUG_LENGTH = 50
LONG_NAME_LENGTH = 50
DESCRIPTION_LENGTH = 500
STRING_VALUE_LENGTH = 400
FREETEXT_LENGTH = 100
PREFIX_SUFFIX_LENGTH = 20
DELIMITER_LENGTH = 1
UTM_LENGTH = 30

# Status choices - used across multiple models


class StatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"

# Submission-specific status choices


class SubmissionStatusChoices(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"

# Dimension type choices


class DimensionTypeChoices(models.TextChoices):
    LIST = "list", "List"
    FREE_TEXT = "text", "Free Text"


# File upload paths
WORKSPACE_LOGO_UPLOAD_PATH = 'workspaces/logos/'
DEFAULT_WORKSPACE_LOGO = "workspaces/default/default-workspace-logo.png"
