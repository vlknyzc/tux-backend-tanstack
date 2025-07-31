"""
Unit tests for Phase 4 batch operations.
Tests batch updates, inheritance analysis, and conflict resolution.
"""

import json
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from ..models import (
    Workspace, Platform, Field, Rule, RuleDetail, Dimension, DimensionValue,
    Submission, String, StringDetail, StringModification, StringUpdateBatch
)
from ..services.batch_update_service import BatchUpdateService, BatchUpdateError
from ..services.inheritance_service import InheritanceService, InheritanceError
from ..services.conflict_resolution_service import ConflictResolutionService

User = get_user_model()


class BatchUpdateServiceTest(TestCase):
    """Test cases for BatchUpdateService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )
        
        self.platform = Platform.objects.create(
            name='Test Platform',
            slug='test-platform',
            workspace=self.workspace
        )
        
        self.field = Field.objects.create(
            name='Test Field',
            field_level=1,
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.rule = Rule.objects.create(
            name='Test Rule',
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.dimension = Dimension.objects.create(
            name='Test Dimension',
            type='list',
            workspace=self.workspace
        )
        
        self.submission = Submission.objects.create(
            name='Test Submission',
            rule=self.rule,
            workspace=self.workspace,
            created_by=self.user
        )
        
        self.string = String.objects.create(
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='test-string-value',
            workspace=self.workspace
        )

    def test_analyze_impact_basic(self):
        """Test basic impact analysis."""
        updates = [
            {
                'string_id': self.string.id,
                'field_updates': {'field_test': 'new_value'}
            }
        ]
        
        result = BatchUpdateService.analyze_impact(self.workspace, updates, depth=5)
        
        self.assertIn('impact', result)
        self.assertIn('affected_strings', result)
        self.assertIn('warnings', result)
        self.assertIn('blockers', result)
        self.assertEqual(result['impact']['direct_updates'], 1)

    def test_analyze_impact_missing_string(self):
        """Test impact analysis with missing string."""
        updates = [
            {
                'string_id': 99999,  # Non-existent string
                'field_updates': {'field_test': 'new_value'}
            }
        ]
        
        with self.assertRaises(BatchUpdateError):
            BatchUpdateService.analyze_impact(self.workspace, updates)

    def test_batch_update_dry_run(self):
        """Test batch update in dry run mode."""
        updates = [
            {
                'string_id': self.string.id,
                'field_updates': {'field_test': 'new_value'},
                'metadata': {'original_string_uuid': str(self.string.string_uuid)}
            }
        ]
        
        options = {'dry_run': True, 'validate_inheritance': True}
        
        result = BatchUpdateService.batch_update_strings(
            self.workspace, updates, self.user, options
        )
        
        self.assertTrue(result['success'])
        self.assertTrue(result['dry_run'])
        self.assertEqual(len(result['updated_strings']), 0)

    def test_get_string_history_empty(self):
        """Test getting history for string with no modifications."""
        result = BatchUpdateService.get_string_history(self.string.id, self.workspace)
        
        self.assertIn('history', result)
        self.assertEqual(len(result['history']), 0)

    def test_get_string_history_not_found(self):
        """Test getting history for non-existent string."""
        with self.assertRaises(BatchUpdateError):
            BatchUpdateService.get_string_history(99999, self.workspace)


class InheritanceServiceTest(TestCase):
    """Test cases for InheritanceService."""

    def setUp(self):
        """Set up test data with parent-child relationship."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )
        
        self.platform = Platform.objects.create(
            name='Test Platform',
            slug='test-platform',
            workspace=self.workspace
        )
        
        self.field = Field.objects.create(
            name='Test Field',
            field_level=1,
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.rule = Rule.objects.create(
            name='Test Rule',
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.submission = Submission.objects.create(
            name='Test Submission',
            rule=self.rule,
            workspace=self.workspace,
            created_by=self.user
        )
        
        # Create parent string
        self.parent_string = String.objects.create(
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='parent-string',
            workspace=self.workspace
        )
        
        # Create child string
        self.child_string = String.objects.create(
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='child-string',
            parent=self.parent_string,
            workspace=self.workspace
        )

    def test_analyze_inheritance_impact_with_children(self):
        """Test inheritance impact analysis with children."""
        updates = [
            {
                'string_id': self.parent_string.id,
                'field_updates': {'field_test': 'new_value'}
            }
        ]
        
        result = InheritanceService.analyze_inheritance_impact(
            [self.parent_string], updates, max_depth=5
        )
        
        self.assertIn('affected_strings', result)
        self.assertIn('warnings', result)
        self.assertIn('blockers', result)

    def test_validate_inheritance_constraints_empty(self):
        """Test inheritance constraint validation with empty updates."""
        result = InheritanceService.validate_inheritance_constraints([], self.workspace)
        
        self.assertEqual(len(result), 0)

    def test_validate_inheritance_constraints_invalid_string(self):
        """Test inheritance constraint validation with invalid string ID."""
        updates = [
            {
                'string_id': 99999,
                'field_updates': {'field_test': 'new_value'}
            }
        ]
        
        result = InheritanceService.validate_inheritance_constraints(updates, self.workspace)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['error_type'], 'not_found')


class ConflictResolutionServiceTest(TestCase):
    """Test cases for ConflictResolutionService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )
        
        self.platform = Platform.objects.create(
            name='Test Platform',
            slug='test-platform',
            workspace=self.workspace
        )
        
        self.field = Field.objects.create(
            name='Test Field',
            field_level=1,
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.rule = Rule.objects.create(
            name='Test Rule',
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.submission = Submission.objects.create(
            name='Test Submission',
            rule=self.rule,
            workspace=self.workspace,
            created_by=self.user
        )
        
        self.string = String.objects.create(
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='test-string',
            workspace=self.workspace
        )

    def test_detect_batch_conflicts_empty(self):
        """Test conflict detection with empty updates."""
        conflicts = ConflictResolutionService.detect_batch_conflicts(
            [], [], self.workspace
        )
        
        self.assertEqual(len(conflicts), 0)

    def test_resolve_conflict_skip(self):
        """Test resolving conflict with skip strategy."""
        conflict = {
            'string_id': self.string.id,
            'conflict_type': 'validation',
            'message': 'Test conflict'
        }
        
        result = ConflictResolutionService.resolve_conflict(
            conflict, 'skip'
        )
        
        self.assertEqual(result['resolution'], 'skipped')
        self.assertEqual(result['string_id'], self.string.id)

    def test_resolve_conflict_take_mine(self):
        """Test resolving conflict with take_mine strategy."""
        conflict = {
            'string_id': self.string.id,
            'conflict_type': 'concurrent_edit',
            'message': 'Test conflict'
        }
        
        result = ConflictResolutionService.resolve_conflict(
            conflict, 'take_mine'
        )
        
        self.assertEqual(result['resolution'], 'take_mine')

    def test_get_suggested_resolutions_concurrent_edit(self):
        """Test getting suggested resolutions for concurrent edit conflict."""
        conflict = {
            'string_id': self.string.id,
            'conflict_type': 'concurrent_edit',
            'message': 'Test conflict'
        }
        
        suggestions = ConflictResolutionService.get_suggested_resolutions(conflict)
        
        self.assertGreater(len(suggestions), 0)
        suggestion_types = [s['type'] for s in suggestions]
        self.assertIn('take_mine', suggestion_types)
        self.assertIn('take_theirs', suggestion_types)

    def test_auto_resolve_conflicts(self):
        """Test automatic conflict resolution."""
        conflicts = [
            {
                'string_id': self.string.id,
                'conflict_type': 'validation',
                'message': 'Test validation conflict'
            },
            {
                'string_id': self.string.id,
                'conflict_type': 'concurrent_edit',
                'message': 'Test concurrent edit conflict'
            }
        ]
        
        auto_resolution_rules = {
            'validation': 'skip',
            'concurrent_edit': 'take_mine'
        }
        
        results = ConflictResolutionService.auto_resolve_conflicts(
            conflicts, auto_resolution_rules
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['resolution'], 'skipped')
        self.assertEqual(results[1]['resolution'], 'take_mine')


class BatchOperationsAPITest(APITestCase):
    """Test cases for batch operations API endpoints."""

    def setUp(self):
        """Set up test data and authentication."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )
        
        # Mock workspace access
        self.user.has_workspace_access = MagicMock(return_value=True)
        
        self.platform = Platform.objects.create(
            name='Test Platform',
            slug='test-platform',
            workspace=self.workspace
        )
        
        self.field = Field.objects.create(
            name='Test Field',
            field_level=1,
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.rule = Rule.objects.create(
            name='Test Rule',
            platform=self.platform,
            workspace=self.workspace
        )
        
        self.submission = Submission.objects.create(
            name='Test Submission',
            rule=self.rule,
            workspace=self.workspace,
            created_by=self.user
        )
        
        self.string = String.objects.create(
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='test-string',
            workspace=self.workspace
        )
        
        self.client.force_authenticate(user=self.user)

    @patch('master_data.views.string_views.BatchUpdateService.batch_update_strings')
    def test_batch_update_endpoint_success(self, mock_batch_update):
        """Test successful batch update API endpoint."""
        mock_batch_update.return_value = {
            'success': True,
            'updated_strings': [self.string.id],
            'affected_strings': [self.string.id],
            'inheritance_updates': [],
            'conflicts': [],
            'backup_id': None,
            'errors': []
        }
        
        data = {
            'updates': [
                {
                    'string_id': self.string.id,
                    'field_updates': {'field_test': 'new_value'},
                    'metadata': {'original_string_uuid': str(self.string.string_uuid)}
                }
            ],
            'options': {
                'dry_run': True,
                'validate_inheritance': True
            }
        }
        
        with patch('master_data.views.string_views.getattr', return_value=self.workspace):
            response = self.client.put('/api/v1/strings/batch_update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('master_data.views.string_views.BatchUpdateService.analyze_impact')
    def test_analyze_impact_endpoint_success(self, mock_analyze_impact):
        """Test successful impact analysis API endpoint."""
        mock_analyze_impact.return_value = {
            'impact': {
                'direct_updates': 1,
                'inheritance_updates': 0,
                'total_affected': 1,
                'max_depth': 0
            },
            'affected_strings': [
                {
                    'string_id': self.string.id,
                    'string_value': self.string.value,
                    'parent_string_id': None,
                    'level': 0,
                    'update_type': 'direct',
                    'affected_fields': ['field_test'],
                    'new_values': {'field_test': 'new_value'},
                    'children': []
                }
            ],
            'warnings': [],
            'blockers': []
        }
        
        data = {
            'updates': [
                {
                    'string_id': self.string.id,
                    'field_updates': {'field_test': 'new_value'}
                }
            ],
            'depth': 5
        }
        
        with patch('master_data.views.string_views.getattr', return_value=self.workspace):
            response = self.client.post('/api/v1/strings/analyze_impact/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['impact']['direct_updates'], 1)

    @patch('master_data.views.string_views.BatchUpdateService.get_string_history')
    def test_string_history_endpoint_success(self, mock_get_history):
        """Test successful string history API endpoint."""
        mock_get_history.return_value = {
            'history': []
        }
        
        with patch('master_data.views.string_views.getattr', return_value=self.workspace):
            response = self.client.get(f'/api/v1/strings/{self.string.id}/history/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('history', response.data)

    def test_batch_update_endpoint_no_workspace(self):
        """Test batch update endpoint without workspace context."""
        data = {
            'updates': [
                {
                    'string_id': self.string.id,
                    'field_updates': {'field_test': 'new_value'}
                }
            ]
        }
        
        with patch('master_data.views.string_views.getattr', return_value=None):
            response = self.client.put('/api/v1/strings/batch_update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_batch_update_endpoint_invalid_data(self):
        """Test batch update endpoint with invalid data."""
        data = {
            'updates': []  # Empty updates list
        }
        
        with patch('master_data.views.string_views.getattr', return_value=self.workspace):
            response = self.client.put('/api/v1/strings/batch_update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)