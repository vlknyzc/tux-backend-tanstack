"""
Tests for enhanced string propagation signal handlers.
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from master_data.models import (
    Workspace, Platform, Field, Rule, RuleDetail,
    Dimension, DimensionValue, Submission, String, StringDetail,
    PropagationJob, PropagationError
)
from master_data.signals.string_propagation import (
    _detect_stringdetail_changes,
    _execute_enhanced_propagation,
    _log_propagation_error,
    _pre_save_state
)

User = get_user_model()


class EnhancedStringPropagationTestCase(TestCase):
    """Test case for enhanced string propagation signal handlers."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        # Create workspace
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            status='active'
        )

        # Create platform
        self.platform = Platform.objects.create(
            name='Test Platform',
            slug='test-platform'
        )

        # Create field
        self.field = Field.objects.create(
            platform=self.platform,
            name='Test Field',
            field_level=1
        )

        # Create dimension
        self.dimension = Dimension.objects.create(
            workspace=self.workspace,
            name='Brand',
            dimension_type='list'
        )

        # Create dimension values
        self.brand_nike = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension,
            value='Nike',
            label='Nike Brand'
        )
        self.brand_adidas = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension,
            value='Adidas',
            label='Adidas Brand'
        )

        # Create rule
        self.rule = Rule.objects.create(
            workspace=self.workspace,
            platform=self.platform,
            name='Test Rule'
        )

        # Create submission
        self.submission = Submission.objects.create(
            workspace=self.workspace,
            rule=self.rule,
            name='Test Submission',
            created_by=self.user
        )

        # Create string
        self.string = String.objects.create(
            workspace=self.workspace,
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='Nike-Test',
            is_auto_generated=True
        )

        # Create string detail
        self.string_detail = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.string,
            dimension=self.dimension,
            dimension_value=self.brand_nike
        )

    def test_detect_stringdetail_changes_with_state(self):
        """Test change detection when pre-save state is available."""
        # Simulate pre-save state
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': self.brand_nike.id,
            'dimension_value_freetext': None,
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Update the string detail
        self.string_detail.dimension_value = self.brand_adidas
        
        # Detect changes
        changes = _detect_stringdetail_changes(self.string_detail)
        
        self.assertIn('dimension_value', changes)
        self.assertEqual(changes['dimension_value']['old'], self.brand_nike.id)
        self.assertEqual(changes['dimension_value']['new'], self.brand_adidas.id)
        self.assertEqual(changes['dimension_value']['old_display'], 'Nike')
        self.assertEqual(changes['dimension_value']['new_display'], 'Adidas')

    def test_detect_stringdetail_changes_no_state(self):
        """Test fallback when no pre-save state is available."""
        # Ensure no pre-save state
        _pre_save_state.pop(self.string_detail.pk, None)
        
        # Update the string detail
        self.string_detail.dimension_value = self.brand_adidas
        
        # Detect changes (should fallback to assuming all fields changed)
        changes = _detect_stringdetail_changes(self.string_detail)
        
        # Should have fallback changes
        self.assertIn('dimension_value', changes)
        self.assertIn('dimension_value_freetext', changes)

    def test_detect_freetext_changes(self):
        """Test detection of freetext changes."""
        # Setup pre-save state
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': None,
            'dimension_value_freetext': 'Old Text',
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Update freetext
        self.string_detail.dimension_value = None
        self.string_detail.dimension_value_freetext = 'New Text'
        
        changes = _detect_stringdetail_changes(self.string_detail)
        
        self.assertIn('dimension_value_freetext', changes)
        self.assertEqual(changes['dimension_value_freetext']['old'], 'Old Text')
        self.assertEqual(changes['dimension_value_freetext']['new'], 'New Text')

    def test_no_changes_detected(self):
        """Test when no actual changes are detected."""
        # Setup pre-save state with same values
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': self.brand_nike.id,
            'dimension_value_freetext': None,
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Don't change anything
        
        changes = _detect_stringdetail_changes(self.string_detail)
        
        self.assertEqual(len(changes), 0)

    @override_settings(MASTER_DATA_CONFIG={'AUTO_REGENERATE_STRINGS': True})
    @patch('master_data.signals.string_propagation._execute_enhanced_propagation')
    def test_signal_handler_triggers_propagation(self, mock_execute):
        """Test that the signal handler triggers enhanced propagation."""
        # Setup pre-save state
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': self.brand_nike.id,
            'dimension_value_freetext': None,
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Update the string detail (this should trigger the signal)
        self.string_detail.dimension_value = self.brand_adidas
        self.string_detail.save()
        
        # Should have called enhanced propagation
        mock_execute.assert_called_once()

    @override_settings(MASTER_DATA_CONFIG={'AUTO_REGENERATE_STRINGS': False})
    @patch('master_data.signals.string_propagation._execute_enhanced_propagation')
    def test_signal_handler_disabled(self, mock_execute):
        """Test that signal handler is disabled when configured."""
        # Update the string detail
        self.string_detail.dimension_value = self.brand_adidas
        self.string_detail.save()
        
        # Should not have called enhanced propagation
        mock_execute.assert_not_called()

    @patch('master_data.signals.string_propagation.PropagationService._analyze_string_hierarchy_impact')
    def test_execute_enhanced_propagation_creates_job(self, mock_analyze):
        """Test that enhanced propagation creates a PropagationJob."""
        mock_analyze.return_value = {
            'affected_strings': [{'string_id': self.string.id, 'level': 0}],
            'warnings': [],
            'blockers': [],
            'max_depth': 1
        }
        
        changed_fields = {
            'dimension_value': {
                'old': self.brand_nike.id,
                'new': self.brand_adidas.id
            }
        }
        
        config = {
            'ENABLE_INHERITANCE_PROPAGATION': True,
            'MAX_INHERITANCE_DEPTH': 10
        }
        
        # Execute enhanced propagation
        _execute_enhanced_propagation(self.string_detail, changed_fields, config)
        
        # Should have created a job
        jobs = PropagationJob.objects.filter(
            workspace=self.workspace,
            metadata__trigger_type='stringdetail_update'
        )
        self.assertEqual(jobs.count(), 1)
        
        job = jobs.first()
        self.assertEqual(job.status, 'completed')
        self.assertIsNone(job.triggered_by)  # System-triggered

    def test_log_propagation_error_creates_record(self):
        """Test that error logging creates PropagationError records."""
        # Create a job first
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            status='running'
        )
        
        # Log an error
        _log_propagation_error(
            self.string_detail,
            "Test error message",
            "test_error_type",
            job=job
        )
        
        # Should have created error record
        errors = PropagationError.objects.filter(job=job)
        self.assertEqual(errors.count(), 1)
        
        error = errors.first()
        self.assertEqual(error.error_message, "Test error message")
        self.assertEqual(error.error_type, "test_error_type")
        self.assertEqual(error.string_detail, self.string_detail)
        self.assertEqual(error.string, self.string_detail.string)

    def test_log_propagation_error_without_instance(self):
        """Test error logging without StringDetail instance."""
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            status='running'
        )
        
        _log_propagation_error(
            None,
            "General error message",
            "general_error",
            job=job,
            string_id=self.string.id
        )
        
        errors = PropagationError.objects.filter(job=job)
        self.assertEqual(errors.count(), 1)
        
        error = errors.first()
        self.assertEqual(error.string, self.string)
        self.assertIsNone(error.string_detail)

    @patch('master_data.signals.string_propagation.logger')
    def test_log_propagation_error_handles_exceptions(self, mock_logger):
        """Test that error logging handles its own exceptions gracefully."""
        # Try to log error without workspace (should fail gracefully)
        _log_propagation_error(
            None,
            "Test error",
            "test_error_type"
        )
        
        # Should have logged a warning about missing workspace
        mock_logger.warning.assert_called()

    def test_recursion_guard_prevents_infinite_loop(self):
        """Test that recursion guard prevents infinite loops."""
        # Set recursion guard
        self.string_detail._regenerating = True
        
        # Setup pre-save state
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': self.brand_nike.id,
            'dimension_value_freetext': None,
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Update should not trigger propagation due to guard
        self.string_detail.dimension_value = self.brand_adidas
        self.string_detail.save()
        
        # Should not have created any jobs due to recursion guard
        jobs = PropagationJob.objects.filter(workspace=self.workspace)
        self.assertEqual(jobs.count(), 0)

    @override_settings(MASTER_DATA_CONFIG={'STRICT_AUTO_REGENERATION': True})
    @patch('master_data.signals.string_propagation._execute_enhanced_propagation')
    def test_strict_mode_raises_exceptions(self, mock_execute):
        """Test that strict mode raises exceptions instead of logging them."""
        # Make the propagation fail
        mock_execute.side_effect = Exception("Test error")
        
        # Setup pre-save state
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': self.brand_nike.id,
            'dimension_value_freetext': None,
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Update should raise exception in strict mode
        self.string_detail.dimension_value = self.brand_adidas
        
        with self.assertRaises(Exception):
            self.string_detail.save()

    @override_settings(MASTER_DATA_CONFIG={'STRICT_AUTO_REGENERATION': False})
    @patch('master_data.signals.string_propagation._execute_enhanced_propagation')
    @patch('master_data.signals.string_propagation.logger')
    def test_non_strict_mode_logs_exceptions(self, mock_logger, mock_execute):
        """Test that non-strict mode logs exceptions instead of raising them."""
        # Make the propagation fail
        mock_execute.side_effect = Exception("Test error")
        
        # Setup pre-save state
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': self.brand_nike.id,
            'dimension_value_freetext': None,
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Update should not raise exception in non-strict mode
        self.string_detail.dimension_value = self.brand_adidas
        self.string_detail.save()  # Should not raise
        
        # Should have logged the error
        mock_logger.error.assert_called()

    def test_pre_save_state_cleanup(self):
        """Test that pre-save state is cleaned up after processing."""
        # Setup pre-save state
        _pre_save_state[self.string_detail.pk] = {
            'dimension_value_id': self.brand_nike.id,
            'dimension_value_freetext': None,
            'string_id': self.string.id,
            'dimension_id': self.dimension.id
        }
        
        # Update the string detail
        self.string_detail.dimension_value = self.brand_adidas
        self.string_detail.save()
        
        # Pre-save state should be cleaned up
        self.assertNotIn(self.string_detail.pk, _pre_save_state)

    def test_created_instance_skips_processing(self):
        """Test that newly created instances skip propagation processing."""
        # Create a new string detail (not update)
        new_string_detail = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.string,
            dimension=self.dimension,
            dimension_value=self.brand_adidas
        )
        
        # Should not have created any propagation jobs for new instance
        jobs = PropagationJob.objects.filter(
            workspace=self.workspace,
            metadata__stringdetail_id=new_string_detail.id
        )
        self.assertEqual(jobs.count(), 0)