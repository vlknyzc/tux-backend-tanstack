"""
Tests for String Registry Service.

These tests verify external string validation, parsing, and hierarchy management.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from master_data import models
from master_data.services import StringRegistryService, StringRegistryValidationError
from master_data.constants import DimensionTypeChoices

User = get_user_model()


class StringRegistryServiceTestCase(TestCase):
    """Test StringRegistryService validation and parsing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create workspace
        self.workspace = models.Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace"
        )

        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create platform
        self.platform = models.Platform.objects.create(
            name="Meta Ads",
            slug="meta-ads",
            platform_type="advertising"
        )

        # Create entities with hierarchy
        self.account_entity = models.Entity.objects.create(
            name="account",
            platform=self.platform,
            entity_level=0
        )
        self.campaign_entity = models.Entity.objects.create(
            name="campaign",
            platform=self.platform,
            entity_level=1,
        )
        self.adgroup_entity = models.Entity.objects.create(
            name="ad_group",
            platform=self.platform,
            entity_level=2,
        )

        # Link entity hierarchy
        self.account_entity.next_entity = self.campaign_entity
        self.account_entity.save()
        self.campaign_entity.next_entity = self.adgroup_entity
        self.campaign_entity.save()

        # Create dimensions
        self.region_dim = models.Dimension.objects.create(
            name="region",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user
        )
        self.quarter_dim = models.Dimension.objects.create(
            name="quarter",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user
        )
        self.objective_dim = models.Dimension.objects.create(
            name="objective",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user
        )

        # Create dimension values
        self.us_value = models.DimensionValue.objects.create(
            dimension=self.region_dim,
            value="US",
            label="United States",
            utm="us",
            workspace=self.workspace,
            created_by=self.user
        )
        self.q4_value = models.DimensionValue.objects.create(
            dimension=self.quarter_dim,
            value="Q4",
            label="Quarter 4",
            utm="q4",
            workspace=self.workspace,
            created_by=self.user
        )
        self.awareness_value = models.DimensionValue.objects.create(
            dimension=self.objective_dim,
            value="Awareness",
            label="Brand Awareness",
            utm="awareness",
            workspace=self.workspace,
            created_by=self.user
        )

        # Create rule for campaign entity
        self.rule = models.Rule.objects.create(
            name="Meta Campaign Standard",
            slug="meta-campaign-standard",
            platform=self.platform,
            workspace=self.workspace,
            status='active',
            created_by=self.user
        )

        # Create rule details with delimiters
        self.region_detail = models.RuleDetail.objects.create(
            rule=self.rule,
            entity=self.campaign_entity,
            dimension=self.region_dim,
            dimension_order=1,
            delimiter="-",
            is_required=True,
            workspace=self.workspace,
            created_by=self.user
        )
        self.quarter_detail = models.RuleDetail.objects.create(
            rule=self.rule,
            entity=self.campaign_entity,
            dimension=self.quarter_dim,
            dimension_order=2,
            delimiter="-",
            is_required=True,
            workspace=self.workspace,
            created_by=self.user
        )
        self.objective_detail = models.RuleDetail.objects.create(
            rule=self.rule,
            entity=self.campaign_entity,
            dimension=self.objective_dim,
            dimension_order=3,
            delimiter="",  # No delimiter after last segment
            is_required=True,
            workspace=self.workspace,
            created_by=self.user
        )

    def test_parse_string_by_rule_success(self):
        """Test successful string parsing using rule pattern."""
        string_value = "US-Q4-Awareness"

        result = StringRegistryService._parse_string_by_rule(
            string_value=string_value,
            rule=self.rule,
            entity=self.campaign_entity
        )

        self.assertEqual(result['region'], 'US')
        self.assertEqual(result['quarter'], 'Q4')
        self.assertEqual(result['objective'], 'Awareness')

    def test_parse_string_missing_delimiter(self):
        """Test parsing fails when delimiter is missing."""
        string_value = "USQ4Awareness"  # Missing delimiters

        with self.assertRaises(StringRegistryValidationError) as context:
            StringRegistryService._parse_string_by_rule(
                string_value=string_value,
                rule=self.rule,
                entity=self.campaign_entity
            )

        self.assertIn('delimiter', str(context.exception))

    def test_parse_string_with_prefix_suffix(self):
        """Test parsing with prefix and suffix."""
        # Update rule detail to have prefix and suffix
        self.region_detail.prefix = "REG_"
        self.region_detail.suffix = "_END"
        self.region_detail.save()

        string_value = "REG_US_END-Q4-Awareness"

        result = StringRegistryService._parse_string_by_rule(
            string_value=string_value,
            rule=self.rule,
            entity=self.campaign_entity
        )

        self.assertEqual(result['region'], 'US')

    def test_validate_external_string_entity_not_found(self):
        """Test validation fails when entity doesn't exist for platform."""
        result = StringRegistryService.validate_external_string(
            workspace=self.workspace,
            platform=self.platform,
            rule=self.rule,
            entity_name="invalid_entity",
            string_value="US-Q4-Awareness"
        )

        self.assertFalse(result['is_valid'])
        self.assertTrue(len(result['errors']) > 0)
        self.assertEqual(result['errors'][0]['type'], 'entity_platform_mismatch')

    def test_validate_external_string_entity_rule_mismatch(self):
        """Test validation when entity doesn't match rule's entity."""
        result = StringRegistryService.validate_external_string(
            workspace=self.workspace,
            platform=self.platform,
            rule=self.rule,
            entity_name="ad_group",  # Rule is for campaign
            string_value="US-Q4-Awareness"
        )

        self.assertFalse(result['is_valid'])
        self.assertTrue(result.get('should_skip'))
        self.assertEqual(result['errors'][0]['type'], 'entity_rule_mismatch')

    def test_validate_external_string_success(self):
        """Test successful external string validation."""
        result = StringRegistryService.validate_external_string(
            workspace=self.workspace,
            platform=self.platform,
            rule=self.rule,
            entity_name="campaign",
            string_value="US-Q4-Awareness",
            external_platform_id="campaign_123"
        )

        self.assertTrue(result['is_valid'])
        self.assertEqual(result['entity'].name, 'campaign')
        self.assertEqual(len(result['errors']), 0)
        self.assertIn('region', result['parsed_dimension_values'])

    def test_validate_external_string_invalid_dimension_value(self):
        """Test validation fails for invalid dimension value."""
        result = StringRegistryService.validate_external_string(
            workspace=self.workspace,
            platform=self.platform,
            rule=self.rule,
            entity_name="campaign",
            string_value="INVALID-Q4-Awareness",  # INVALID region
            external_platform_id="campaign_123"
        )

        self.assertFalse(result['is_valid'])
        error_types = [e['type'] for e in result['errors']]
        self.assertIn('invalid_dimension_value', error_types)

    def test_validate_external_string_too_long(self):
        """Test validation fails for strings exceeding max length."""
        long_string = "A" * 501  # Exceeds 500 char limit

        result = StringRegistryService.validate_external_string(
            workspace=self.workspace,
            platform=self.platform,
            rule=self.rule,
            entity_name="campaign",
            string_value=long_string
        )

        self.assertFalse(result['is_valid'])
        error_types = [e['type'] for e in result['errors']]
        self.assertIn('string_too_long', error_types)

    def test_strip_prefix_suffix(self):
        """Test prefix and suffix stripping."""
        result = StringRegistryService._strip_prefix_suffix(
            value="PREFIX_value_SUFFIX",
            prefix="PREFIX_",
            suffix="_SUFFIX"
        )
        self.assertEqual(result, "value")

    def test_strip_prefix_only(self):
        """Test prefix-only stripping."""
        result = StringRegistryService._strip_prefix_suffix(
            value="PREFIX_value",
            prefix="PREFIX_",
            suffix=None
        )
        self.assertEqual(result, "value")

    def test_strip_suffix_only(self):
        """Test suffix-only stripping."""
        result = StringRegistryService._strip_prefix_suffix(
            value="value_SUFFIX",
            prefix=None,
            suffix="_SUFFIX"
        )
        self.assertEqual(result, "value")

    def test_validate_hierarchy_parent_not_found(self):
        """Test hierarchy validation when parent doesn't exist."""
        result = StringRegistryService.validate_hierarchy_relationship(
            child_entity=self.campaign_entity,
            parent_external_id="account_999",
            workspace=self.workspace
        )

        self.assertIsNone(result['parent_string'])
        self.assertTrue(len(result['warnings']) > 0)
        self.assertEqual(result['warnings'][0]['type'], 'parent_not_found')

    def test_validate_hierarchy_invalid_entity_level(self):
        """Test hierarchy validation fails for invalid entity levels."""
        # Create parent string with ad_group entity (level 2)
        parent_string = models.String.objects.create(
            workspace=self.workspace,
            entity=self.adgroup_entity,  # Level 2
            rule=self.rule,
            value="Parent-String",
            external_platform_id="adgroup_123",
            validation_source='external',
            created_by=self.user
        )

        # Try to validate campaign (level 1) as child of ad_group (level 2) - INVALID
        result = StringRegistryService.validate_hierarchy_relationship(
            child_entity=self.campaign_entity,  # Level 1
            parent_external_id="adgroup_123",
            workspace=self.workspace
        )

        self.assertTrue(len(result['errors']) > 0)
        self.assertEqual(result['errors'][0]['type'], 'invalid_entity_level')

    def test_validate_hierarchy_missing_intermediate_level(self):
        """Test warning for missing intermediate entity levels."""
        # Create parent string with account entity (level 0)
        parent_string = models.String.objects.create(
            workspace=self.workspace,
            entity=self.account_entity,  # Level 0
            rule=self.rule,
            value="Account-String",
            external_platform_id="account_123",
            validation_source='external',
            created_by=self.user
        )

        # Validate ad_group (level 2) as child of account (level 0)
        # Missing campaign (level 1)
        result = StringRegistryService.validate_hierarchy_relationship(
            child_entity=self.adgroup_entity,  # Level 2
            parent_external_id="account_123",
            workspace=self.workspace
        )

        self.assertTrue(len(result['warnings']) > 0)
        self.assertEqual(result['warnings'][0]['type'], 'missing_intermediate_level')

    def test_validate_hierarchy_success(self):
        """Test successful hierarchy validation."""
        # Create parent string with campaign entity (level 1)
        parent_string = models.String.objects.create(
            workspace=self.workspace,
            entity=self.campaign_entity,  # Level 1
            rule=self.rule,
            value="Campaign-String",
            external_platform_id="campaign_123",
            validation_source='external',
            created_by=self.user
        )

        # Validate ad_group (level 2) as child of campaign (level 1) - VALID
        result = StringRegistryService.validate_hierarchy_relationship(
            child_entity=self.adgroup_entity,  # Level 2
            parent_external_id="campaign_123",
            workspace=self.workspace
        )

        self.assertIsNotNone(result['parent_string'])
        self.assertEqual(result['parent_string'].id, parent_string.id)
        self.assertEqual(len(result['errors']), 0)


class StringRegistryServiceWorkspaceIsolationTestCase(TestCase):
    """Test workspace isolation in string registry operations."""

    def setUp(self):
        """Set up test fixtures with multiple workspaces."""
        # Create two workspaces
        self.workspace1 = models.Workspace.objects.create(
            name="Workspace 1",
            slug="workspace-1"
        )
        self.workspace2 = models.Workspace.objects.create(
            name="Workspace 2",
            slug="workspace-2"
        )

        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create platform
        self.platform = models.Platform.objects.create(
            name="Meta Ads",
            slug="meta-ads"
        )

        # Create entity
        self.entity = models.Entity.objects.create(
            name="campaign",
            platform=self.platform,
            entity_level=1
        )

        # Create string in workspace 1
        self.rule1 = models.Rule.objects.create(
            name="Rule 1",
            slug="rule-1",
            platform=self.platform,
            workspace=self.workspace1,
            status='active',
            created_by=self.user
        )

        self.string1 = models.String.objects.create(
            workspace=self.workspace1,
            entity=self.entity,
            rule=self.rule1,
            value="String-WS1",
            external_platform_id="campaign_123",
            validation_source='external',
            created_by=self.user
        )

    def test_hierarchy_validation_respects_workspace_isolation(self):
        """Test that hierarchy validation only finds parents in same workspace."""
        # Try to find parent from workspace1 while querying in workspace2
        result = StringRegistryService.validate_hierarchy_relationship(
            child_entity=self.entity,
            parent_external_id="campaign_123",  # Exists in workspace1
            workspace=self.workspace2  # But querying in workspace2
        )

        # Should not find the parent (workspace isolation)
        self.assertIsNone(result['parent_string'])
        self.assertTrue(len(result['warnings']) > 0)
        self.assertEqual(result['warnings'][0]['type'], 'parent_not_found')
