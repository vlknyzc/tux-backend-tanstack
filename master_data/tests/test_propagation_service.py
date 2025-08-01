"""
Tests for PropagationService functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from master_data.models import (
    Workspace, Platform, Field, Rule, RuleDetail,
    Dimension, DimensionValue, Submission, String, StringDetail,
    PropagationJob, PropagationError
)
from master_data.services.propagation_service import PropagationService, PropagationError as PropagationServiceError

User = get_user_model()


class PropagationServiceTestCase(TestCase):
    """Test case for PropagationService functionality."""

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

        # Create fields
        self.field1 = Field.objects.create(
            platform=self.platform,
            name='Level 1 Field',
            field_level=1
        )
        self.field2 = Field.objects.create(
            platform=self.platform,
            name='Level 2 Field',
            field_level=2
        )

        # Create dimensions
        self.dimension1 = Dimension.objects.create(
            workspace=self.workspace,
            name='Brand',
            dimension_type='list'
        )
        self.dimension2 = Dimension.objects.create(
            workspace=self.workspace,
            name='Campaign',
            dimension_type='list'
        )

        # Create dimension values
        self.brand_nike = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension1,
            value='Nike',
            label='Nike Brand'
        )
        self.brand_adidas = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension1,
            value='Adidas',
            label='Adidas Brand'
        )
        self.campaign_summer = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension2,
            value='Summer2024',
            label='Summer 2024 Campaign'
        )

        # Create rule
        self.rule = Rule.objects.create(
            workspace=self.workspace,
            platform=self.platform,
            name='Test Rule'
        )

        # Create rule details
        RuleDetail.objects.create(
            workspace=self.workspace,
            rule=self.rule,
            field=self.field1,
            dimension=self.dimension1,
            delimiter='-',
            dimension_order=1,
            is_required=True
        )
        RuleDetail.objects.create(
            workspace=self.workspace,
            rule=self.rule,
            field=self.field1,
            dimension=self.dimension2,
            delimiter='-',
            dimension_order=2,
            is_required=True
        )

        # Create submission
        self.submission = Submission.objects.create(
            workspace=self.workspace,
            rule=self.rule,
            name='Test Submission',
            created_by=self.user
        )

        # Create parent string
        self.parent_string = String.objects.create(
            workspace=self.workspace,
            submission=self.submission,
            field=self.field1,
            rule=self.rule,
            value='Nike-Summer2024',
            is_auto_generated=True
        )

        # Create child string
        self.child_string = String.objects.create(
            workspace=self.workspace,
            submission=self.submission,
            field=self.field2,
            rule=self.rule,
            value='Nike-Summer2024-Child',
            parent=self.parent_string,
            is_auto_generated=True
        )

        # Create string details for parent
        self.parent_detail1 = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.parent_string,
            dimension=self.dimension1,
            dimension_value=self.brand_nike
        )
        self.parent_detail2 = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.parent_string,
            dimension=self.dimension2,
            dimension_value=self.campaign_summer
        )

        # Create string details for child
        self.child_detail1 = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.child_string,
            dimension=self.dimension1,
            dimension_value=self.brand_nike
        )
        self.child_detail2 = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.child_string,
            dimension=self.dimension2,
            dimension_value=self.campaign_summer
        )

    def test_detect_field_changes(self):
        """Test detection of field changes in StringDetail updates."""
        # Test dimension_value change
        update_data = {
            'dimension_value': self.brand_adidas.id
        }
        
        changed_fields = PropagationService._detect_field_changes(
            self.parent_detail1, update_data
        )
        
        self.assertIn('dimension_value', changed_fields)
        self.assertEqual(changed_fields['dimension_value']['old'], self.brand_nike.id)
        self.assertEqual(changed_fields['dimension_value']['new'], self.brand_adidas.id)

    def test_detect_freetext_changes(self):
        """Test detection of freetext changes."""
        update_data = {
            'dimension_value_freetext': 'New Freetext Value'
        }
        
        changed_fields = PropagationService._detect_field_changes(
            self.parent_detail1, update_data
        )
        
        self.assertIn('dimension_value_freetext', changed_fields)
        self.assertEqual(changed_fields['dimension_value_freetext']['new'], 'New Freetext Value')

    def test_no_changes_detected(self):
        """Test when no changes are detected."""
        update_data = {
            'dimension_value': self.brand_nike.id  # Same as current
        }
        
        changed_fields = PropagationService._detect_field_changes(
            self.parent_detail1, update_data
        )
        
        self.assertEqual(len(changed_fields), 0)

    def test_analyze_impact_single_string(self):
        """Test impact analysis for a single string update."""
        updates = [{
            'string_detail_id': self.parent_detail1.id,
            'dimension_value': self.brand_adidas.id
        }]
        
        impact = PropagationService.analyze_impact(updates, self.workspace, max_depth=5)
        
        self.assertIn('affected_strings', impact)
        self.assertIn('warnings', impact)
        self.assertIn('conflicts', impact)
        self.assertIn('summary', impact)
        
        # Should affect parent and child
        self.assertGreaterEqual(len(impact['affected_strings']), 2)

    def test_analyze_impact_with_child_strings(self):
        """Test impact analysis includes child strings."""
        updates = [{
            'string_detail_id': self.parent_detail1.id,
            'dimension_value': self.brand_adidas.id
        }]
        
        impact = PropagationService.analyze_impact(updates, self.workspace, max_depth=5)
        
        # Find parent and child in affected strings
        string_ids = [s['string_id'] for s in impact['affected_strings']]
        
        self.assertIn(self.parent_string.id, string_ids)
        self.assertIn(self.child_string.id, string_ids)

    def test_analyze_impact_depth_limit(self):
        """Test that impact analysis respects depth limits."""
        updates = [{
            'string_detail_id': self.parent_detail1.id,
            'dimension_value': self.brand_adidas.id
        }]
        
        # Limit depth to 1 (should only include parent)
        impact = PropagationService.analyze_impact(updates, self.workspace, max_depth=1)
        
        # Should have limited depth analysis
        self.assertLessEqual(impact['summary']['max_depth'], 1)

    @patch('master_data.services.propagation_service.PropagationService._calculate_new_string_value')
    def test_calculate_new_string_value_called(self, mock_calculate):
        """Test that new string value calculation is called."""
        mock_calculate.return_value = 'Adidas-Summer2024'
        
        updates = [{
            'string_detail_id': self.parent_detail1.id,
            'dimension_value': self.brand_adidas.id
        }]
        
        PropagationService.analyze_impact(updates, self.workspace, max_depth=5)
        
        # Should have been called for parent string
        self.assertTrue(mock_calculate.called)

    def test_check_value_conflict(self):
        """Test conflict detection for duplicate values."""
        # Create another string with same rule/field/workspace
        conflicting_string = String.objects.create(
            workspace=self.workspace,
            submission=self.submission,
            field=self.field1,
            rule=self.rule,
            value='Adidas-Summer2024',  # This would be the new value
            is_auto_generated=True
        )
        
        conflict = PropagationService._check_value_conflict(
            self.parent_string, 'Adidas-Summer2024', self.workspace
        )
        
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict['type'], 'duplicate_value')
        self.assertEqual(conflict['conflicting_string_id'], conflicting_string.id)

    def test_no_conflict_different_field(self):
        """Test no conflict when same value exists for different field."""
        # Create string with same value but different field
        String.objects.create(
            workspace=self.workspace,
            submission=self.submission,
            field=self.field2,  # Different field
            rule=self.rule,
            value='Adidas-Summer2024',
            is_auto_generated=True
        )
        
        conflict = PropagationService._check_value_conflict(
            self.parent_string, 'Adidas-Summer2024', self.workspace
        )
        
        self.assertIsNone(conflict)

    def test_generate_inherited_changes(self):
        """Test generation of inherited changes for child strings."""
        parent_changes = {
            'dimension_value': {
                'old': self.brand_nike.id,
                'new': self.brand_adidas.id,
                'old_display': 'Nike',
                'new_display': 'Adidas'
            }
        }
        
        inherited = PropagationService._generate_inherited_changes(
            self.child_string, parent_changes
        )
        
        # Should inherit the dimension_value change
        self.assertIn('dimension_value', inherited)
        self.assertEqual(inherited['dimension_value']['new'], self.brand_adidas.id)

    def test_should_inherit_field_default(self):
        """Test default field inheritance behavior."""
        # By default, should inherit most fields
        should_inherit = PropagationService._should_inherit_field(
            self.child_string, 'dimension_value'
        )
        
        self.assertTrue(should_inherit)

    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        estimate = PropagationService._estimate_processing_time(
            total_affected=50, max_depth=3
        )
        
        self.assertIn('duration', estimate)
        self.assertIn('method', estimate)
        self.assertIn('background_required', estimate)
        self.assertIsInstance(estimate['estimated_seconds'], float)

    def test_estimate_background_required(self):
        """Test that large operations are marked for background processing."""
        estimate = PropagationService._estimate_processing_time(
            total_affected=200, max_depth=5
        )
        
        self.assertTrue(estimate['background_required'])
        self.assertEqual(estimate['method'], 'background')

    def test_deduplicate_affected_strings(self):
        """Test deduplication of affected strings list."""
        affected_strings = [
            {'string_id': 1, 'value': 'test1'},
            {'string_id': 2, 'value': 'test2'},
            {'string_id': 1, 'value': 'test1'},  # Duplicate
            {'string_id': 3, 'value': 'test3'},
        ]
        
        unique = PropagationService._deduplicate_affected_strings(affected_strings)
        
        self.assertEqual(len(unique), 3)
        string_ids = [s['string_id'] for s in unique]
        self.assertEqual(string_ids, [1, 2, 3])

    def test_execute_propagation_creates_job(self):
        """Test that execute_propagation creates a PropagationJob."""
        updates = [{
            'string_detail_id': self.parent_detail1.id,
            'dimension_value': self.brand_adidas.id
        }]
        
        result = PropagationService.execute_propagation(
            updates, self.workspace, self.user, {}
        )
        
        self.assertIn('job_id', result)
        
        # Verify job was created
        job = PropagationJob.objects.get(batch_id=result['job_id'])
        self.assertEqual(job.workspace, self.workspace)
        self.assertEqual(job.triggered_by, self.user)

    def test_execute_propagation_with_options(self):
        """Test execute_propagation with various options."""
        updates = [{
            'string_detail_id': self.parent_detail1.id,
            'dimension_value': self.brand_adidas.id
        }]
        
        options = {
            'max_depth': 5,
            'error_handling': 'continue'
        }
        
        result = PropagationService.execute_propagation(
            updates, self.workspace, self.user, options
        )
        
        self.assertIn('job_id', result)
        self.assertIn('successful_updates', result)
        self.assertIn('total_affected', result)

    def test_error_handling_invalid_string_detail(self):
        """Test error handling for invalid StringDetail ID."""
        updates = [{
            'string_detail_id': 99999,  # Non-existent ID
            'dimension_value': self.brand_adidas.id
        }]
        
        with self.assertRaises(PropagationServiceError):
            PropagationService.execute_propagation(
                updates, self.workspace, self.user, {}
            )

    def test_analyze_impact_empty_updates(self):
        """Test impact analysis with empty updates list."""
        impact = PropagationService.analyze_impact([], self.workspace, max_depth=5)
        
        self.assertEqual(len(impact['affected_strings']), 0)
        self.assertEqual(impact['summary']['total_affected'], 0)

    def test_analyze_impact_nonexistent_string_detail(self):
        """Test impact analysis with non-existent StringDetail."""
        updates = [{
            'string_detail_id': 99999,  # Non-existent
            'dimension_value': self.brand_adidas.id
        }]
        
        impact = PropagationService.analyze_impact(updates, self.workspace, max_depth=5)
        
        # Should generate warning for not found
        self.assertTrue(any(w['type'] == 'not_found' for w in impact['warnings']))

    @patch('master_data.services.propagation_service.logger')
    def test_logging_on_error(self, mock_logger):
        """Test that errors are properly logged."""
        updates = [{
            'string_detail_id': 'invalid',  # Invalid type
            'dimension_value': self.brand_adidas.id
        }]
        
        with self.assertRaises(PropagationServiceError):
            PropagationService.analyze_impact(updates, self.workspace, max_depth=5)
        
        # Should have logged the error
        mock_logger.error.assert_called()