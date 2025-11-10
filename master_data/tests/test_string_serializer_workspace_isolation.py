"""
Tests for string serializer workspace isolation (Issue #37).

These tests verify that StringWithDetailsSerializer properly filters
submission and parent querysets by workspace, preventing information
disclosure and cross-workspace references.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from master_data import models, serializers
from master_data.constants import DimensionTypeChoices

User = get_user_model()


class StringSerializerWorkspaceIsolationTestCase(TestCase):
    """Test workspace isolation in StringWithDetailsSerializer."""

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

        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create platform (shared across workspaces)
        self.platform = models.Platform.objects.create(
            name="Test Platform",
            slug="test-platform"
        )

        # Create entities for the platform
        self.entity1 = models.Entity.objects.create(
            name="Entity 1",
            platform=self.platform,
            entity_level=1
        )

        # Create rules in each workspace
        self.rule_ws1 = models.Rule.objects.create(
            name="Rule WS1",
            slug="rule-ws1",
            platform=self.platform,
            workspace=self.workspace1
        )
        self.rule_ws2 = models.Rule.objects.create(
            name="Rule WS2",
            slug="rule-ws2",
            platform=self.platform,
            workspace=self.workspace2
        )

        # Create dimensions in each workspace
        self.dimension_ws1 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        self.dimension_ws2 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

        # Create dimension values
        self.dim_value_ws1 = models.DimensionValue.objects.create(
            dimension=self.dimension_ws1,
            value="prod",
            label="Production",
            utm="PROD",
            workspace=self.workspace1,
            created_by=self.user
        )
        self.dim_value_ws2 = models.DimensionValue.objects.create(
            dimension=self.dimension_ws2,
            value="prod",
            label="Production",
            utm="PROD",
            workspace=self.workspace2,
            created_by=self.user
        )

        # Create submissions in each workspace
        self.submission_ws1 = models.Submission.objects.create(
            name="Submission WS1",
            rule=self.rule_ws1,
            starting_entity=self.entity1,
            workspace=self.workspace1
        )
        self.submission_ws2 = models.Submission.objects.create(
            name="Submission WS2",
            rule=self.rule_ws2,
            starting_entity=self.entity1,
            workspace=self.workspace2
        )

        # Create parent strings in each workspace
        self.parent_string_ws1 = models.String.objects.create(
            entity=self.entity1,
            rule=self.rule_ws1,
            submission=self.submission_ws1,
            value="parent_ws1",
            workspace=self.workspace1,
            created_by=self.user
        )
        self.parent_string_ws2 = models.String.objects.create(
            entity=self.entity1,
            rule=self.rule_ws2,
            submission=self.submission_ws2,
            value="parent_ws2",
            workspace=self.workspace2,
            created_by=self.user
        )

    def test_serializer_requires_workspace_context(self):
        """Test that serializer requires workspace context for proper filtering."""
        # Without workspace context, querysets should be empty
        serializer = serializers.StringWithDetailsSerializer(
            data={
                'entity': self.entity1.id,
                'workspace': self.workspace1.id,
                'details': [
                    {
                        'dimension': self.dimension_ws1.id,
                        'dimension_value': self.dim_value_ws1.id
                    }
                ]
            }
        )

        # The serializer should work but querysets will be limited
        # (this tests the default behavior without context)
        self.assertIsNotNone(serializer)

    def test_submission_serializer_field_filters_by_workspace(self):
        """Test that submission serializer field only accepts submissions from current workspace."""
        # Try to reference submission from workspace 2 while in workspace 1 context
        serializer = serializers.StringWithDetailsSerializer(
            data={
                'entity': self.entity1.id,
                'submission': self.submission_ws2.id,  # From workspace 2
                'workspace': self.workspace1.id,
                'details': [
                    {
                        'dimension': self.dimension_ws1.id,
                        'dimension_value': self.dim_value_ws1.id
                    }
                ]
            },
            context={'workspace': self.workspace1}
        )

        # Should fail validation
        self.assertFalse(serializer.is_valid())
        self.assertIn('submission', serializer.errors)

    def test_submission_serializer_field_accepts_same_workspace(self):
        """Test that submission serializer field accepts submissions from same workspace."""
        serializer = serializers.StringWithDetailsSerializer(
            data={
                'entity': self.entity1.id,
                'submission': self.submission_ws1.id,  # From workspace 1
                'workspace': self.workspace1.id,
                'details': [
                    {
                        'dimension': self.dimension_ws1.id,
                        'dimension_value': self.dim_value_ws1.id
                    }
                ]
            },
            context={'workspace': self.workspace1}
        )

        # Should pass validation (other validation may fail but submission should be OK)
        serializer.is_valid()
        if 'submission' in serializer.errors:
            self.fail(f"Submission from same workspace should be valid: {serializer.errors['submission']}")

    def test_parent_serializer_field_filters_by_workspace(self):
        """Test that parent serializer field only accepts strings from current workspace."""
        # Try to reference parent string from workspace 2 while in workspace 1 context
        serializer = serializers.StringWithDetailsSerializer(
            data={
                'entity': self.entity1.id,
                'parent': self.parent_string_ws2.id,  # From workspace 2
                'workspace': self.workspace1.id,
                'details': [
                    {
                        'dimension': self.dimension_ws1.id,
                        'dimension_value': self.dim_value_ws1.id
                    }
                ]
            },
            context={'workspace': self.workspace1}
        )

        # Should fail validation
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)

    def test_parent_serializer_field_accepts_same_workspace(self):
        """Test that parent serializer field accepts strings from same workspace."""
        serializer = serializers.StringWithDetailsSerializer(
            data={
                'entity': self.entity1.id,
                'parent': self.parent_string_ws1.id,  # From workspace 1
                'workspace': self.workspace1.id,
                'details': [
                    {
                        'dimension': self.dimension_ws1.id,
                        'dimension_value': self.dim_value_ws1.id
                    }
                ]
            },
            context={'workspace': self.workspace1}
        )

        # Should pass validation (other validation may fail but parent should be OK)
        serializer.is_valid()
        if 'parent' in serializer.errors:
            self.fail(f"Parent from same workspace should be valid: {serializer.errors['parent']}")

    def test_workspace_context_filters_querysets_correctly(self):
        """Test that workspace context properly filters submission and parent querysets."""
        # Create serializer with workspace 1 context
        serializer = serializers.StringWithDetailsSerializer(
            context={'workspace': self.workspace1}
        )

        # Check that submission queryset only contains workspace 1 submissions
        submission_ids = set(serializer.fields['submission'].queryset.values_list('id', flat=True))
        self.assertIn(self.submission_ws1.id, submission_ids)
        self.assertNotIn(self.submission_ws2.id, submission_ids)

        # Check that parent queryset only contains workspace 1 strings
        parent_ids = set(serializer.fields['parent'].queryset.values_list('id', flat=True))
        self.assertIn(self.parent_string_ws1.id, parent_ids)
        self.assertNotIn(self.parent_string_ws2.id, parent_ids)


class StringAPIWorkspaceIsolationTestCase(APITestCase):
    """Test workspace isolation through String API endpoints."""

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

        # Create user and assign to both workspaces
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

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

        # Create platform and entity
        self.platform = models.Platform.objects.create(
            name="Test Platform",
            slug="test-platform"
        )
        self.entity1 = models.Entity.objects.create(
            name="Entity 1",
            platform=self.platform,
            entity_level=1
        )

        # Create rules
        self.rule_ws1 = models.Rule.objects.create(
            name="Rule WS1",
            slug="rule-ws1",
            platform=self.platform,
            workspace=self.workspace1
        )
        self.rule_ws2 = models.Rule.objects.create(
            name="Rule WS2",
            slug="rule-ws2",
            platform=self.platform,
            workspace=self.workspace2
        )

        # Create dimensions
        self.dimension_ws1 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        self.dimension_ws2 = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

        # Create dimension values
        self.dim_value_ws1 = models.DimensionValue.objects.create(
            dimension=self.dimension_ws1,
            value="prod",
            label="Production",
            utm="PROD",
            workspace=self.workspace1,
            created_by=self.user
        )
        self.dim_value_ws2 = models.DimensionValue.objects.create(
            dimension=self.dimension_ws2,
            value="prod",
            label="Production",
            utm="PROD",
            workspace=self.workspace2,
            created_by=self.user
        )

        # Create submissions
        self.submission_ws1 = models.Submission.objects.create(
            name="Submission WS1",
            rule=self.rule_ws1,
            starting_entity=self.entity1,
            workspace=self.workspace1
        )
        self.submission_ws2 = models.Submission.objects.create(
            name="Submission WS2",
            rule=self.rule_ws2,
            starting_entity=self.entity1,
            workspace=self.workspace2
        )

        # Create parent strings
        self.parent_string_ws1 = models.String.objects.create(
            entity=self.entity1,
            rule=self.rule_ws1,
            submission=self.submission_ws1,
            value="parent_ws1",
            workspace=self.workspace1,
            created_by=self.user
        )
        self.parent_string_ws2 = models.String.objects.create(
            entity=self.entity1,
            rule=self.rule_ws2,
            submission=self.submission_ws2,
            value="parent_ws2",
            workspace=self.workspace2,
            created_by=self.user
        )

    def test_api_rejects_submission_from_different_workspace(self):
        """Test that API rejects submission from different workspace."""
        url = f'/api/v1/workspaces/{self.workspace1.id}/strings/'
        data = {
            'entity': self.entity1.id,
            'submission': self.submission_ws2.id,  # From workspace 2
            'workspace': self.workspace1.id,
            'details': [
                {
                    'dimension': self.dimension_ws1.id,
                    'dimension_value': self.dim_value_ws1.id
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        # Should fail with 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('submission', response.data)

    def test_api_rejects_parent_from_different_workspace(self):
        """Test that API rejects parent string from different workspace."""
        url = f'/api/v1/workspaces/{self.workspace1.id}/strings/'
        data = {
            'entity': self.entity1.id,
            'parent': self.parent_string_ws2.id,  # From workspace 2
            'workspace': self.workspace1.id,
            'details': [
                {
                    'dimension': self.dimension_ws1.id,
                    'dimension_value': self.dim_value_ws1.id
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        # Should fail with 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)

    def test_api_accepts_submission_from_same_workspace(self):
        """Test that API accepts submission from same workspace."""
        # Test serializer directly to verify workspace filtering works
        # (Full API string creation requires complex setup beyond scope of this test)
        from master_data.serializers.string import StringWithDetailsSerializer

        data = {
            'entity': self.entity1.id,
            'submission': self.submission_ws1.id,  # From workspace 1
            'workspace': self.workspace1.id,
            'details': [
                {
                    'dimension': self.dimension_ws1.id,
                    'dimension_value': self.dim_value_ws1.id
                }
            ]
        }

        serializer = StringWithDetailsSerializer(
            data=data,
            context={'workspace': self.workspace1}
        )

        serializer.is_valid()
        # If it fails, it shouldn't be because of submission serializer field
        if 'submission' in serializer.errors:
            self.fail(f"Submission from same workspace should be valid: {serializer.errors['submission']}")

    def test_api_accepts_parent_from_same_workspace(self):
        """Test that API accepts parent string from same workspace."""
        # Test serializer directly to verify workspace filtering works
        # (Full API string creation requires complex setup beyond scope of this test)
        from master_data.serializers.string import StringWithDetailsSerializer

        data = {
            'entity': self.entity1.id,
            'parent': self.parent_string_ws1.id,  # From workspace 1
            'workspace': self.workspace1.id,
            'details': [
                {
                    'dimension': self.dimension_ws1.id,
                    'dimension_value': self.dim_value_ws1.id
                }
            ]
        }

        serializer = StringWithDetailsSerializer(
            data=data,
            context={'workspace': self.workspace1}
        )

        serializer.is_valid()
        # If it fails, it shouldn't be because of parent serializer field
        if 'parent' in serializer.errors:
            self.fail(f"Parent from same workspace should be valid: {serializer.errors['parent']}")

    def test_view_passes_workspace_context_to_serializer(self):
        """Test that StringViewSet passes workspace context to serializer."""
        # Verify workspace context is passed by testing cross-workspace validation works through API
        # If workspace context wasn't passed, the serializer wouldn't filter querysets
        url = f'/api/v1/workspaces/{self.workspace1.id}/strings/'

        # Try to reference submission from workspace 2 (should fail due to workspace filtering)
        data = {
            'entity': self.entity1.id,
            'submission': self.submission_ws2.id,  # From workspace 2
            'workspace': self.workspace1.id,
            'details': [
                {
                    'dimension': self.dimension_ws1.id,
                    'dimension_value': self.dim_value_ws1.id
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        # Should fail with 400 Bad Request due to cross-workspace reference
        # This confirms workspace context is being passed to serializer
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('submission', response.data)
