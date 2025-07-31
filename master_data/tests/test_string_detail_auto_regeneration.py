"""
Tests for StringDetail auto-regeneration functionality.
"""

from django.test import TestCase, override_settings
from django.db import transaction
from unittest.mock import patch, MagicMock
import logging

from master_data.models import (
    Workspace, Platform, Field, Rule, RuleDetail,
    Dimension, DimensionValue, Submission, String, StringDetail
)
from users.models import UserAccount


class StringDetailAutoRegenerationTests(TestCase):
    """Test automatic string regeneration when StringDetail records are updated."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = UserAccount.objects.create_user(
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
        self.brand_value = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension1,
            value='Nike',
            label='Nike Brand'
        )
        self.campaign_value = DimensionValue.objects.create(
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
            field=self.field,
            dimension=self.dimension1,
            prefix='',
            suffix='',
            delimiter='-',
            dimension_order=1,
            is_required=True
        )
        RuleDetail.objects.create(
            workspace=self.workspace,
            rule=self.rule,
            field=self.field,
            dimension=self.dimension2,
            prefix='',
            suffix='',
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

        # Create string
        self.string = String.objects.create(
            workspace=self.workspace,
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='Nike-Summer2024',
            is_auto_generated=True
        )

        # Create string details
        self.string_detail1 = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.string,
            dimension=self.dimension1,
            dimension_value=self.brand_value
        )
        self.string_detail2 = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.string,
            dimension=self.dimension2,
            dimension_value=self.campaign_value
        )

    @override_settings(MASTER_DATA_CONFIG={'AUTO_REGENERATE_STRINGS': True})
    def test_string_regenerates_on_detail_update(self):
        """Test that string value updates when StringDetail changes."""
        # Create new dimension value
        new_campaign_value = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension2,
            value='Winter2024',
            label='Winter 2024 Campaign'
        )

        # Update StringDetail
        original_string_value = self.string.value
        self.string_detail2.dimension_value = new_campaign_value
        self.string_detail2.save()

        # Refresh string from database
        self.string.refresh_from_db()

        # Verify string value was regenerated
        self.assertNotEqual(self.string.value, original_string_value)
        self.assertEqual(self.string.value, 'Nike-Winter2024')

    @override_settings(MASTER_DATA_CONFIG={'AUTO_REGENERATE_STRINGS': False})
    def test_no_regeneration_when_disabled(self):
        """Test that string doesn't regenerate when feature is disabled."""
        # Create new dimension value
        new_campaign_value = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension2,
            value='Winter2024',
            label='Winter 2024 Campaign'
        )

        # Update StringDetail
        original_string_value = self.string.value
        self.string_detail2.dimension_value = new_campaign_value
        self.string_detail2.save()

        # Refresh string from database
        self.string.refresh_from_db()

        # Verify string value was NOT regenerated
        self.assertEqual(self.string.value, original_string_value)

    @override_settings(MASTER_DATA_CONFIG={'AUTO_REGENERATE_STRINGS': True})
    def test_no_regeneration_on_detail_creation(self):
        """Test that new StringDetail doesn't trigger regeneration."""
        # Create new dimension and string detail
        new_dimension = Dimension.objects.create(
            workspace=self.workspace,
            name='Region',
            dimension_type='list'
        )

        original_string_value = self.string.value

        # Create new StringDetail (should not trigger regeneration)
        StringDetail.objects.create(
            workspace=self.workspace,
            string=self.string,
            dimension=new_dimension,
            dimension_value_freetext='US'
        )

        # Refresh string from database
        self.string.refresh_from_db()

        # Verify string value was NOT regenerated (since it's creation, not update)
        self.assertEqual(self.string.value, original_string_value)

    @override_settings(MASTER_DATA_CONFIG={
        'AUTO_REGENERATE_STRINGS': True,
        'ENABLE_INHERITANCE_PROPAGATION': True,
        'MAX_INHERITANCE_DEPTH': 2
    })
    def test_inheritance_propagation(self):
        """Test that child strings are updated when parent changes."""
        # Create child string
        child_string = String.objects.create(
            workspace=self.workspace,
            submission=self.submission,
            field=self.field,
            rule=self.rule,
            value='Nike-Summer2024-Child',
            parent=self.string,
            is_auto_generated=True
        )

        # Create child string details (same dimensions for simplicity)
        StringDetail.objects.create(
            workspace=self.workspace,
            string=child_string,
            dimension=self.dimension1,
            dimension_value=self.brand_value
        )
        StringDetail.objects.create(
            workspace=self.workspace,
            string=child_string,
            dimension=self.dimension2,
            dimension_value=self.campaign_value
        )

        # Create new dimension value
        new_brand_value = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension1,
            value='Adidas',
            label='Adidas Brand'
        )

        # Update parent StringDetail
        original_child_value = child_string.value
        self.string_detail1.dimension_value = new_brand_value
        self.string_detail1.save()

        # Refresh strings from database
        self.string.refresh_from_db()
        child_string.refresh_from_db()

        # Verify both parent and child were regenerated
        self.assertEqual(self.string.value, 'Adidas-Summer2024')
        # Child should also be regenerated (inheritance propagation)
        self.assertNotEqual(child_string.value, original_child_value)

    @override_settings(MASTER_DATA_CONFIG={
        'AUTO_REGENERATE_STRINGS': True,
        'STRICT_AUTO_REGENERATION': False
    })
    @patch('master_data.models.string.logger')
    def test_error_handling_non_strict_mode(self, mock_logger):
        """Test that errors are logged but don't raise exceptions in non-strict mode."""
        # Mock the regenerate_value method to raise an exception
        with patch.object(String, 'regenerate_value', side_effect=Exception('Test error')):
            # Update StringDetail - should not raise exception
            self.string_detail1.dimension_value_freetext = 'New Value'
            try:
                self.string_detail1.save()
                # Should not raise exception
            except Exception:
                self.fail("Exception was raised in non-strict mode")

        # Verify error was logged
        mock_logger.error.assert_called()

    @override_settings(MASTER_DATA_CONFIG={
        'AUTO_REGENERATE_STRINGS': True,
        'STRICT_AUTO_REGENERATION': True
    })
    def test_error_handling_strict_mode(self):
        """Test that errors raise exceptions in strict mode."""
        # Mock the regenerate_value method to raise an exception
        with patch.object(String, 'regenerate_value', side_effect=Exception('Test error')):
            # Update StringDetail - should raise exception
            self.string_detail1.dimension_value_freetext = 'New Value'
            with self.assertRaises(Exception):
                self.string_detail1.save()

    @override_settings(MASTER_DATA_CONFIG={'AUTO_REGENERATE_STRINGS': True})
    def test_circular_dependency_prevention(self):
        """Test that infinite recursion is prevented."""
        # Set recursion guard manually to simulate recursion
        self.string_detail1._regenerating = True

        original_value = self.string.value

        # Update StringDetail - should be skipped due to recursion guard
        new_brand_value = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension1,
            value='Puma',
            label='Puma Brand'
        )
        self.string_detail1.dimension_value = new_brand_value
        self.string_detail1.save()

        # Refresh string from database
        self.string.refresh_from_db()

        # Verify string value was NOT regenerated due to recursion guard
        self.assertEqual(self.string.value, original_value)

        # Clean up
        delattr(self.string_detail1, '_regenerating')
