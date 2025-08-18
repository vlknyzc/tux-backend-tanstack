"""
RESTful API views for submissions, strings, and string details.
These views are now organized into separate modules for better maintainability.
This file imports from the split modules for backward compatibility.
"""

# Import all viewsets and filters from the split modules
from .mixins import WorkspaceValidationMixin
from .submission_views import (
    SubmissionWorkspaceFilter,
    SubmissionViewSet,
    SubmissionStringViewSet
)
from .string_views import (
    StringWorkspaceFilter,
    StringViewSet
)
from .string_detail_views import (
    StringDetailWorkspaceFilter,
    StringDetailViewSet,
    StringDetailNestedViewSet
)

# Maintain backward compatibility by exposing all classes at module level
__all__ = [
    'WorkspaceValidationMixin',
    'SubmissionWorkspaceFilter',
    'SubmissionViewSet',
    'SubmissionStringViewSet',
    'StringWorkspaceFilter',
    'StringViewSet',
    'StringDetailWorkspaceFilter',
    'StringDetailViewSet',
    'StringDetailNestedViewSet',
]
