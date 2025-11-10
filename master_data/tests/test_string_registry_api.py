"""
Integration tests for String Registry API endpoints.

These tests verify the CSV upload and single validation API endpoints.
"""
import csv
import io
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from master_data import models
from master_data.constants import DimensionTypeChoices
from users.models import WorkspaceUser

User = get_user_model()


class StringRegistryAPITestCase(TestCase):
    """Test String Registry API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        # Create workspace
        self.workspace = models.Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace"
        )

        # Create user and assign to workspace
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='admin'
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

        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _create_csv_file(self, rows):
        """Helper to create a CSV file in memory."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['entity_name', 'string_value', 'external_platform_id', 'parent_external_id'])
        writer.writeheader()
        writer.writerows(rows)
        output.seek(0)

        # Convert to BytesIO for file upload
        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        csv_bytes.name = 'test.csv'
        return csv_bytes

    def test_upload_csv_success(self):
        """Test successful CSV upload with valid strings."""
        csv_data = [
            {
                'entity_name': 'campaign',
                'string_value': 'US-Q4-Awareness',
                'external_platform_id': 'campaign_123',
                'parent_external_id': ''
            }
        ]
        csv_file = self._create_csv_file(csv_data)

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': csv_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['summary']['total_rows'], 1)
        self.assertEqual(response.data['summary']['valid'], 1)
        self.assertEqual(response.data['summary']['failed'], 0)

        # Verify string was created in database
        string = models.String.objects.get(
            external_platform_id='campaign_123',
            workspace=self.workspace
        )
        self.assertEqual(string.value, 'US-Q4-Awareness')
        self.assertEqual(string.validation_source, 'external')
        self.assertEqual(string.validation_status, 'valid')

    def test_upload_csv_invalid_dimension_value(self):
        """Test CSV upload with invalid dimension value."""
        csv_data = [
            {
                'entity_name': 'campaign',
                'string_value': 'INVALID-Q4-Awareness',
                'external_platform_id': 'campaign_456',
                'parent_external_id': ''
            }
        ]
        csv_file = self._create_csv_file(csv_data)

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': csv_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['summary']['failed'], 1)

        # Check error details
        result = response.data['results'][0]
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any(e['type'] == 'invalid_dimension_value' for e in result['errors']))

    def test_upload_csv_duplicate_external_id(self):
        """Test CSV upload with duplicate external_platform_id."""
        # Create existing string
        existing_string = models.String.objects.create(
            workspace=self.workspace,
            entity=self.campaign_entity,
            rule=self.rule,
            value="US-Q4-Awareness",
            external_platform_id="campaign_123",
            validation_source='external',
            validation_status='valid',
            created_by=self.user
        )

        # Upload CSV with same external_platform_id but different value
        csv_data = [
            {
                'entity_name': 'campaign',
                'string_value': 'US-Q4-Awareness',  # Same value - should update
                'external_platform_id': 'campaign_123',
                'parent_external_id': ''
            }
        ]
        csv_file = self._create_csv_file(csv_data)

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': csv_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['updated'], 1)

        # Verify string was updated, not duplicated
        string_count = models.String.objects.filter(
            external_platform_id='campaign_123',
            workspace=self.workspace
        ).count()
        self.assertEqual(string_count, 1)

    def test_upload_csv_with_hierarchy(self):
        """Test CSV upload with parent-child relationships."""
        csv_data = [
            {
                'entity_name': 'account',
                'string_value': 'US-Q4-Awareness',
                'external_platform_id': 'account_123',
                'parent_external_id': ''
            },
            {
                'entity_name': 'campaign',
                'string_value': 'US-Q4-Awareness',
                'external_platform_id': 'campaign_123',
                'parent_external_id': 'account_123'
            }
        ]
        csv_file = self._create_csv_file(csv_data)

        # Create rule for account entity
        account_rule = models.Rule.objects.create(
            name="Meta Account Standard",
            slug="meta-account-standard",
            platform=self.platform,
            workspace=self.workspace,
            status='active',
            created_by=self.user
        )
        models.RuleDetail.objects.create(
            rule=account_rule,
            entity=self.account_entity,
            dimension=self.region_dim,
            dimension_order=1,
            delimiter="-",
            is_required=True,
            workspace=self.workspace,
            created_by=self.user
        )
        models.RuleDetail.objects.create(
            rule=account_rule,
            entity=self.account_entity,
            dimension=self.quarter_dim,
            dimension_order=2,
            delimiter="-",
            is_required=True,
            workspace=self.workspace,
            created_by=self.user
        )
        models.RuleDetail.objects.create(
            rule=account_rule,
            entity=self.account_entity,
            dimension=self.objective_dim,
            dimension_order=3,
            delimiter="",
            is_required=True,
            workspace=self.workspace,
            created_by=self.user
        )

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': account_rule.id,  # Use account rule
            'file': csv_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify both strings were created
        account_string = models.String.objects.get(external_platform_id='account_123')
        campaign_string = models.String.objects.get(external_platform_id='campaign_123')

        # Verify parent relationship
        self.assertEqual(campaign_string.external_parent_id, 'account_123')

    def test_upload_csv_missing_required_columns(self):
        """Test CSV upload with missing required columns."""
        csv_data = [
            {
                'entity_name': 'campaign',
                'string_value': 'US-Q4-Awareness',
                # Missing external_platform_id
            }
        ]

        # Manually create CSV with missing column
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['entity_name', 'string_value'])
        writer.writeheader()
        writer.writerows(csv_data)
        output.seek(0)
        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        csv_bytes.name = 'test.csv'

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': csv_bytes
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('external_platform_id', str(response.data))

    def test_upload_csv_invalid_file_type(self):
        """Test CSV upload with non-CSV file."""
        # Create a text file instead of CSV
        text_file = io.BytesIO(b'This is not a CSV file')
        text_file.name = 'test.txt'

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': text_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_csv_entity_rule_mismatch(self):
        """Test CSV upload where entity doesn't match rule."""
        csv_data = [
            {
                'entity_name': 'ad_group',  # Rule is for campaign
                'string_value': 'US-Q4-Awareness',
                'external_platform_id': 'adgroup_123',
                'parent_external_id': ''
            }
        ]
        csv_file = self._create_csv_file(csv_data)

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': csv_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(result['status'], 'skipped')
        self.assertTrue(any(e['type'] == 'entity_rule_mismatch' for e in result['errors']))

    def test_validate_single_success(self):
        """Test single string validation endpoint."""
        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/validate_single/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'entity_name': 'campaign',
            'string_value': 'US-Q4-Awareness',
            'external_platform_id': 'campaign_test_123'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        self.assertEqual(response.data['entity']['name'], 'campaign')
        self.assertEqual(len(response.data['errors']), 0)
        self.assertIn('region', response.data['parsed_dimension_values'])

    def test_validate_single_invalid_value(self):
        """Test single string validation with invalid dimension value."""
        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/validate_single/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'entity_name': 'campaign',
            'string_value': 'INVALID-Q4-Awareness',
            'external_platform_id': 'campaign_test_456'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_valid'])
        self.assertTrue(any(e['type'] == 'invalid_dimension_value' for e in response.data['errors']))

    def test_upload_csv_unauthorized(self):
        """Test CSV upload without authentication."""
        self.client.force_authenticate(user=None)

        csv_data = [
            {
                'entity_name': 'campaign',
                'string_value': 'US-Q4-Awareness',
                'external_platform_id': 'campaign_123',
                'parent_external_id': ''
            }
        ]
        csv_file = self._create_csv_file(csv_data)

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': csv_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_csv_string_too_long(self):
        """Test CSV upload with string exceeding max length."""
        long_string = "A" * 501
        csv_data = [
            {
                'entity_name': 'campaign',
                'string_value': long_string,
                'external_platform_id': 'campaign_long',
                'parent_external_id': ''
            }
        ]
        csv_file = self._create_csv_file(csv_data)

        url = f'/api/v1/workspaces/{self.workspace.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule.id,
            'file': csv_file
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any(e['type'] == 'string_too_long' for e in result['errors']))


class StringRegistryAPIWorkspaceIsolationTestCase(TestCase):
    """Test workspace isolation in String Registry API."""

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

        # Create users for each workspace
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        WorkspaceUser.objects.create(
            user=self.user1,
            workspace=self.workspace1,
            role='admin'
        )

        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )
        WorkspaceUser.objects.create(
            user=self.user2,
            workspace=self.workspace2,
            role='admin'
        )

        # Create platform and entity
        self.platform = models.Platform.objects.create(
            name="Meta Ads",
            slug="meta-ads"
        )
        self.entity = models.Entity.objects.create(
            name="campaign",
            platform=self.platform,
            entity_level=1
        )

        # Create dimension in workspace1
        self.dimension = models.Dimension.objects.create(
            name="region",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user1
        )
        self.dim_value = models.DimensionValue.objects.create(
            dimension=self.dimension,
            value="US",
            label="United States",
            workspace=self.workspace1,
            created_by=self.user1
        )

        # Create rule in workspace1
        self.rule1 = models.Rule.objects.create(
            name="Rule 1",
            slug="rule-1",
            platform=self.platform,
            workspace=self.workspace1,
            status='active',
            created_by=self.user1
        )
        models.RuleDetail.objects.create(
            rule=self.rule1,
            entity=self.entity,
            dimension=self.dimension,
            dimension_order=1,
            delimiter="",
            is_required=True,
            workspace=self.workspace1,
            created_by=self.user1
        )

        # Set up API client
        self.client = APIClient()

    def test_upload_csv_respects_workspace_isolation(self):
        """Test that CSV upload only affects the specified workspace."""
        self.client.force_authenticate(user=self.user1)

        # Create CSV data
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['entity_name', 'string_value', 'external_platform_id', 'parent_external_id'])
        writer.writeheader()
        writer.writerow({
            'entity_name': 'campaign',
            'string_value': 'US',
            'external_platform_id': 'campaign_ws1',
            'parent_external_id': ''
        })
        output.seek(0)
        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        csv_bytes.name = 'test.csv'

        url = f'/api/v1/workspaces/{self.workspace1.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule1.id,
            'file': csv_bytes
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify string was created in workspace1
        self.assertTrue(
            models.String.objects.filter(
                external_platform_id='campaign_ws1',
                workspace=self.workspace1
            ).exists()
        )

        # Verify string was NOT created in workspace2
        self.assertFalse(
            models.String.objects.filter(
                external_platform_id='campaign_ws1',
                workspace=self.workspace2
            ).exists()
        )

    def test_user_cannot_access_other_workspace(self):
        """Test that user cannot upload to workspace they don't have access to."""
        self.client.force_authenticate(user=self.user2)  # User2 is in workspace2

        # Try to upload to workspace1
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['entity_name', 'string_value', 'external_platform_id', 'parent_external_id'])
        writer.writeheader()
        writer.writerow({
            'entity_name': 'campaign',
            'string_value': 'US',
            'external_platform_id': 'campaign_test',
            'parent_external_id': ''
        })
        output.seek(0)
        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
        csv_bytes.name = 'test.csv'

        url = f'/api/v1/workspaces/{self.workspace1.id}/string-registry/upload/'
        response = self.client.post(url, {
            'platform_id': self.platform.id,
            'rule_id': self.rule1.id,
            'file': csv_bytes
        }, format='multipart')

        # Should be forbidden or not found
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
