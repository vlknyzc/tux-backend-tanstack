"""
Tests for workspace isolation in serializers.

These tests verify that serializers properly filter data by workspace
to prevent information disclosure and maintain multi-tenant isolation.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from master_data import models
from master_data.serializers import DimensionBulkCreateSerializer, DimensionValueBulkCreateSerializer
from master_data.constants import DimensionTypeChoices
from users.models import WorkspaceUser

User = get_user_model()


class DimensionSerializerWorkspaceIsolationTestCase(TestCase):
    """Test workspace isolation in dimension bulk serializers."""

    def setUp(self):
        """Set up test fixtures."""
        # Create two workspaces
        self.workspace1 = models.Workspace.objects.create(
            name="Workspace 1",
            slug="workspace-1"
        )
        self.workspace2 = models.Workspace.objects.create(
            name="Workspace 2",
            slug="workspace-2"
        )

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create dimensions in workspace 1
        self.dim1_ws1 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        self.dim2_ws1 = models.Dimension.objects.create(
            name="Project",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Create dimension with same name in workspace 2
        self.dim1_ws2 = models.Dimension.objects.create(
            name="Environment",  # Same name as in workspace 1
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

        # Create dimension values in workspace 1
        self.val1_ws1 = models.DimensionValue.objects.create(
            dimension=self.dim1_ws1,
            value="prod",
            label="Production",
            utm="prod",
            workspace=self.workspace1,
            created_by=self.user
        )

        # Create dimension value with same name in workspace 2
        self.val1_ws2 = models.DimensionValue.objects.create(
            dimension=self.dim1_ws2,
            value="prod",  # Same value as in workspace 1
            label="Production",
            utm="prod",
            workspace=self.workspace2,
            created_by=self.user
        )

    def test_dimension_validation_requires_workspace_context(self):
        """Test that dimension validation fails without workspace context."""
        data = {
            'dimensions': [
                {'name': 'NewDim', 'type': DimensionTypeChoices.LIST}
            ]
        }

        serializer = DimensionBulkCreateSerializer(data=data, context={})

        self.assertFalse(serializer.is_valid())
        self.assertIn('dimensions', serializer.errors)
        error_msg = str(serializer.errors['dimensions'])
        self.assertIn('workspace', error_msg.lower())

    def test_dimension_validation_workspace_isolation(self):
        """Test that dimension validation only checks current workspace."""
        # Try to create dimension with same name as in workspace1, but in workspace2
        # This should succeed because they're in different workspaces
        data = {
            'dimensions': [
                {'name': 'Environment', 'type': DimensionTypeChoices.LIST}
            ]
        }

        serializer = DimensionBulkCreateSerializer(
            data=data,
            context={'workspace': self.workspace2}
        )

        # Should be valid because "Environment" already exists in workspace2
        # so validation should pass (it's checking existing dimensions for parent resolution)
        self.assertTrue(serializer.is_valid())

    def test_dimension_parent_resolution_workspace_isolated(self):
        """Test that parent resolution only looks in current workspace."""
        # Try to create dimension with parent from workspace1 while in workspace2
        data = {
            'dimensions': [
                {
                    'name': 'Service',
                    'type': DimensionTypeChoices.LIST,
                    'parent_name': 'Project'  # This exists only in workspace1
                }
            ]
        }

        serializer = DimensionBulkCreateSerializer(
            data=data,
            context={'workspace': self.workspace2}
        )

        # Should fail because 'Project' doesn't exist in workspace2
        self.assertFalse(serializer.is_valid())
        self.assertIn('dimensions', serializer.errors)
        error_msg = str(serializer.errors['dimensions'])
        self.assertIn('Project', error_msg)
        self.assertIn('not found', error_msg.lower())

    def test_dimension_value_validation_requires_workspace_context(self):
        """Test that dimension value validation fails without workspace context."""
        data = {
            'dimension_values': [
                {
                    'dimension_name': 'Environment',
                    'value': 'dev',
                    'label': 'Development',
                    'utm': 'dev'
                }
            ]
        }

        serializer = DimensionValueBulkCreateSerializer(data=data, context={})

        self.assertFalse(serializer.is_valid())
        self.assertIn('dimension_values', serializer.errors)
        error_msg = str(serializer.errors['dimension_values'])
        self.assertIn('workspace', error_msg.lower())

    def test_dimension_value_validation_workspace_isolation(self):
        """Test that dimension value validation only checks current workspace."""
        # Try to create value referencing dimension in correct workspace
        data = {
            'dimension_values': [
                {
                    'dimension_name': 'Environment',
                    'value': 'staging',
                    'label': 'Staging',
                    'utm': 'staging'
                }
            ]
        }

        serializer = DimensionValueBulkCreateSerializer(
            data=data,
            context={'workspace': self.workspace2}
        )

        # Should be valid - finds Environment dimension in workspace2
        self.assertTrue(serializer.is_valid())

    def test_dimension_value_parent_resolution_workspace_isolated(self):
        """Test that dimension value parent resolution is workspace-isolated."""
        # Create a parent dimension value in workspace1
        parent_val_ws1 = models.DimensionValue.objects.create(
            dimension=self.dim1_ws1,
            value="global",
            label="Global",
            utm="global",
            workspace=self.workspace1,
            created_by=self.user
        )

        # Try to reference this parent from workspace2
        data = {
            'dimension_values': [
                {
                    'dimension_name': 'Environment',
                    'value': 'regional',
                    'label': 'Regional',
                    'utm': 'regional',
                    'parent_dimension_name': 'Environment',
                    'parent_value': 'global'  # Exists only in workspace1
                }
            ]
        }

        serializer = DimensionValueBulkCreateSerializer(
            data=data,
            context={'workspace': self.workspace2}
        )

        # Should fail because parent 'global' doesn't exist in workspace2
        self.assertFalse(serializer.is_valid())
        self.assertIn('dimension_values', serializer.errors)
        error_msg = str(serializer.errors['dimension_values'])
        self.assertIn('global', error_msg)
        self.assertIn('not found', error_msg.lower())


class DimensionAPIWorkspaceIsolationTestCase(APITestCase):
    """Test workspace isolation in dimension API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create two workspaces
        self.workspace1 = models.Workspace.objects.create(
            name="Workspace 1",
            slug="workspace-1"
        )
        self.workspace2 = models.Workspace.objects.create(
            name="Workspace 2",
            slug="workspace-2"
        )

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Assign user to both workspaces
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace1,
            role='admin'
        )
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace2,
            role='admin'
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Create dimension in workspace1
        self.dim1_ws1 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )

    def test_bulk_create_dimensions_workspace_isolation(self):
        """Test that bulk create properly isolates by workspace."""
        url = f'/api/v1/workspaces/{self.workspace2.id}/dimensions/bulk_create/'

        # Try to create dimension with same name as workspace1 in workspace2
        data = {
            'dimensions': [
                {
                    'name': 'Environment',  # Same as in workspace1
                    'type': DimensionTypeChoices.LIST,
                    'description': 'Test environment'
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        # Should succeed because workspaces are isolated
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 1)
        self.assertEqual(response.data['error_count'], 0)

        # Verify dimension was created in workspace2
        dimension = models.Dimension.objects.get(
            name='Environment',
            workspace=self.workspace2
        )
        self.assertEqual(dimension.workspace_id, self.workspace2.id)

    def test_bulk_create_dimension_values_workspace_isolation(self):
        """Test that bulk create dimension values properly isolates by workspace."""
        # Create dimension in workspace2
        dim2_ws2 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

        url = f'/api/v1/workspaces/{self.workspace2.id}/dimension-values/bulk_create/'

        data = {
            'dimension_values': [
                {
                    'dimension_name': 'Environment',
                    'value': 'prod',
                    'label': 'Production',
                    'utm': 'prod'
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 1)
        self.assertEqual(response.data['error_count'], 0)

        # Verify value was created in workspace2
        dim_value = models.DimensionValue.objects.get(
            dimension=dim2_ws2,
            value='prod'
        )
        self.assertEqual(dim_value.workspace_id, self.workspace2.id)
