"""
Tests for mass assignment vulnerability prevention (Issue #8).

These tests verify that system-managed fields (workspace, created_by, timestamps)
cannot be set or modified through API requests, preventing authorization bypass
and user impersonation attacks.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from master_data import models
from master_data.constants import DimensionTypeChoices

User = get_user_model()


class DimensionMassAssignmentTestCase(APITestCase):
    """Test mass assignment prevention for Dimension model."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create workspaces
        self.workspace1 = models.Workspace.objects.create(
            name="Workspace 1",
            slug="workspace-1"
        )
        self.workspace2 = models.Workspace.objects.create(
            name="Workspace 2",
            slug="workspace-2"
        )

        # Create users
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

        # Assign user to both workspaces
        from users.models import WorkspaceUser
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

    def test_cannot_assign_to_different_workspace_via_api(self):
        """Test that workspace cannot be set to different workspace via API."""
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimensions/'
        data = {
            'name': 'Test Dimension',
            'type': DimensionTypeChoices.LIST,
            'workspace': self.workspace2.id  # Try to assign to different workspace
        }

        response = self.client.post(url, data, format='json')

        # Should succeed but ignore workspace field
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify dimension was created in workspace1, not workspace2
        dimension = models.Dimension.objects.get(id=response.data['id'])
        self.assertEqual(dimension.workspace.id, self.workspace1.id)
        self.assertNotEqual(dimension.workspace.id, self.workspace2.id)

    def test_cannot_set_created_by_via_api(self):
        """Test that created_by cannot be set to another user via API."""
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimensions/'
        data = {
            'name': 'Test Dimension',
            'type': DimensionTypeChoices.LIST,
            'created_by': self.other_user.id  # Try to impersonate other user
        }

        response = self.client.post(url, data, format='json')

        # Should succeed but ignore created_by field
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify dimension was created by actual user, not other_user
        dimension = models.Dimension.objects.get(id=response.data['id'])
        self.assertEqual(dimension.created_by.id, self.user.id)
        self.assertNotEqual(dimension.created_by.id, self.other_user.id)

    def test_cannot_modify_workspace_via_update(self):
        """Test that workspace cannot be modified via PATCH/PUT."""
        # Create dimension in workspace1
        dimension = models.Dimension.objects.create(
            name="Test Dimension",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )

        url = f'/api/v1/workspaces/{self.workspace1.id}/dimensions/{dimension.id}/'
        data = {
            'workspace': self.workspace2.id  # Try to change workspace
        }

        response = self.client.patch(url, data, format='json')

        # Should succeed but ignore workspace field
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify workspace wasn't changed
        dimension.refresh_from_db()
        self.assertEqual(dimension.workspace.id, self.workspace1.id)
        self.assertNotEqual(dimension.workspace.id, self.workspace2.id)

    def test_workspace_field_is_read_only(self):
        """Test that workspace field is marked as read_only in serializer."""
        from master_data.serializers.dimension import DimensionSerializer

        serializer = DimensionSerializer()
        self.assertIn('workspace', serializer.Meta.read_only_fields)

    def test_created_by_field_is_read_only(self):
        """Test that created_by field is marked as read_only in serializer."""
        from master_data.serializers.dimension import DimensionSerializer

        serializer = DimensionSerializer()
        self.assertIn('created_by', serializer.Meta.read_only_fields)


class DimensionValueMassAssignmentTestCase(APITestCase):
    """Test mass assignment prevention for DimensionValue model."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create workspaces
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
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

        # Assign user to both workspaces
        from users.models import WorkspaceUser
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

        # Create dimensions
        self.dimension1 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        self.dimension2 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_cannot_assign_dimension_value_to_different_workspace(self):
        """Test that workspace cannot be set to different workspace for dimension value."""
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimension-values/'
        data = {
            'dimension': self.dimension1.id,
            'value': 'prod',
            'label': 'Production',
            'utm': 'PROD',
            'workspace': self.workspace2.id  # Try to assign to different workspace
        }

        response = self.client.post(url, data, format='json')

        # Should succeed but ignore workspace field
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify dimension value was created in workspace1
        dim_value = models.DimensionValue.objects.get(id=response.data['id'])
        self.assertEqual(dim_value.workspace.id, self.workspace1.id)
        self.assertNotEqual(dim_value.workspace.id, self.workspace2.id)

    def test_cannot_set_created_by_for_dimension_value(self):
        """Test that created_by cannot be set for dimension value."""
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimension-values/'
        data = {
            'dimension': self.dimension1.id,
            'value': 'prod',
            'label': 'Production',
            'utm': 'PROD',
            'created_by': self.other_user.id  # Try to impersonate
        }

        response = self.client.post(url, data, format='json')

        # Should succeed but ignore created_by field
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify dimension value was created by actual user
        dim_value = models.DimensionValue.objects.get(id=response.data['id'])
        self.assertEqual(dim_value.created_by.id, self.user.id)
        self.assertNotEqual(dim_value.created_by.id, self.other_user.id)

    def test_dimension_value_serializer_has_read_only_fields(self):
        """Test that DimensionValueSerializer has proper read_only_fields."""
        from master_data.serializers.dimension import DimensionValueSerializer

        serializer = DimensionValueSerializer()
        self.assertIn('workspace', serializer.Meta.read_only_fields)
        self.assertIn('created_by', serializer.Meta.read_only_fields)
        self.assertIn('created', serializer.Meta.read_only_fields)
        self.assertIn('last_updated', serializer.Meta.read_only_fields)


class RuleMassAssignmentTestCase(APITestCase):
    """Test mass assignment prevention for Rule model."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create workspaces
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
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )

        # Assign user to both workspaces
        from users.models import WorkspaceUser
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

        # Create platform
        self.platform = models.Platform.objects.create(
            name="Test Platform",
            slug="test-platform"
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_rule_serializer_has_read_only_fields(self):
        """Test that RuleCreateUpdateSerializer has proper read_only_fields."""
        from master_data.serializers.rule import RuleCreateUpdateSerializer

        serializer = RuleCreateUpdateSerializer()
        self.assertIn('workspace', serializer.Meta.read_only_fields)
        self.assertIn('created_by', serializer.Meta.read_only_fields)
        self.assertIn('id', serializer.Meta.read_only_fields)


class StringMassAssignmentTestCase(APITestCase):
    """Test mass assignment prevention for String model."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create workspaces
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

        # Assign user to both workspaces
        from users.models import WorkspaceUser
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace1,
            role='admin'
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

    def test_string_serializer_has_read_only_fields(self):
        """Test that StringWithDetailsSerializer has proper read_only_fields."""
        from master_data.serializers.string import StringWithDetailsSerializer

        serializer = StringWithDetailsSerializer()
        self.assertIn('workspace', serializer.Meta.read_only_fields)
        self.assertIn('created_by', serializer.Meta.read_only_fields)
        self.assertIn('created', serializer.Meta.read_only_fields)
        self.assertIn('last_updated', serializer.Meta.read_only_fields)
        self.assertIn('version', serializer.Meta.read_only_fields)


class BaseSerializerTestCase(TestCase):
    """Test WorkspaceOwnedSerializer base class."""

    def test_workspace_owned_serializer_has_read_only_fields(self):
        """Test that WorkspaceOwnedSerializer defines read_only_fields."""
        from master_data.serializers.base import WorkspaceOwnedSerializer

        self.assertIn('id', WorkspaceOwnedSerializer.Meta.read_only_fields)
        self.assertIn('workspace', WorkspaceOwnedSerializer.Meta.read_only_fields)
        self.assertIn('created_by', WorkspaceOwnedSerializer.Meta.read_only_fields)
        self.assertIn('created', WorkspaceOwnedSerializer.Meta.read_only_fields)
        self.assertIn('last_updated', WorkspaceOwnedSerializer.Meta.read_only_fields)

    def test_all_workspace_serializers_inherit_from_base(self):
        """Test that all workspace-owned serializers inherit from WorkspaceOwnedSerializer."""
        from master_data.serializers.dimension import DimensionSerializer, DimensionValueSerializer
        from master_data.serializers.rule import RuleCreateUpdateSerializer
        from master_data.serializers.string import StringWithDetailsSerializer
        from master_data.serializers.base import WorkspaceOwnedSerializer

        # Check inheritance
        self.assertTrue(issubclass(DimensionSerializer, WorkspaceOwnedSerializer))
        self.assertTrue(issubclass(DimensionValueSerializer, WorkspaceOwnedSerializer))
        self.assertTrue(issubclass(RuleCreateUpdateSerializer, WorkspaceOwnedSerializer))
        self.assertTrue(issubclass(StringWithDetailsSerializer, WorkspaceOwnedSerializer))
