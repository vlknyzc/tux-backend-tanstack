"""
Tests for dimension validation logic consolidation.

These tests verify that validation is properly centralized in the serializer
and model layers, preventing duplicate validation code across views.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError

from master_data import models, serializers
from master_data.constants import DimensionTypeChoices

User = get_user_model()


class DimensionSerializerValidationTestCase(TestCase):
    """Test dimension validation in serializer layer."""

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

        # Create parent dimensions
        self.parent_ws1 = models.Dimension.objects.create(
            name="Parent WS1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        self.parent_ws2 = models.Dimension.objects.create(
            name="Parent WS2",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

    def test_parent_must_be_in_same_workspace(self):
        """Test that parent dimension must be in the same workspace."""
        # Try to create dimension in workspace1 with parent from workspace2
        serializer = serializers.DimensionSerializer(
            data={
                'name': 'Child Dimension',
                'type': DimensionTypeChoices.LIST,
                'parent': self.parent_ws2.id,
                'workspace': self.workspace1.id
            },
            context={'workspace': self.workspace1}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)
        self.assertIn('same workspace', str(serializer.errors['parent']).lower())

    def test_parent_in_same_workspace_is_valid(self):
        """Test that parent in same workspace is accepted."""
        serializer = serializers.DimensionSerializer(
            data={
                'name': 'Child Dimension',
                'type': DimensionTypeChoices.LIST,
                'parent': self.parent_ws1.id,
                'workspace': self.workspace1.id
            },
            context={'workspace': self.workspace1}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_circular_reference_prevented_direct(self):
        """Test that direct circular reference is prevented (A -> A)."""
        # Create a dimension
        dim1 = models.Dimension.objects.create(
            name="Dim1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Try to set its parent to itself
        serializer = serializers.DimensionSerializer(
            dim1,
            data={'parent': dim1.id},
            partial=True,
            context={'workspace': self.workspace1}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)
        self.assertIn('circular', str(serializer.errors['parent']).lower())

    def test_circular_reference_prevented_two_levels(self):
        """Test that circular reference is prevented (A -> B -> A)."""
        # Create dimension hierarchy: dim1 -> dim2
        dim1 = models.Dimension.objects.create(
            name="Dim1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        dim2 = models.Dimension.objects.create(
            name="Dim2",
            type=DimensionTypeChoices.LIST,
            parent=dim1,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Try to set dim1's parent to dim2 (would create circular reference)
        serializer = serializers.DimensionSerializer(
            dim1,
            data={'parent': dim2.id},
            partial=True,
            context={'workspace': self.workspace1}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)
        self.assertIn('circular', str(serializer.errors['parent']).lower())

    def test_circular_reference_prevented_three_levels(self):
        """Test that circular reference is prevented (A -> B -> C -> A)."""
        # Create dimension hierarchy: dim1 -> dim2 -> dim3
        dim1 = models.Dimension.objects.create(
            name="Dim1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        dim2 = models.Dimension.objects.create(
            name="Dim2",
            type=DimensionTypeChoices.LIST,
            parent=dim1,
            workspace=self.workspace1,
            created_by=self.user
        )
        dim3 = models.Dimension.objects.create(
            name="Dim3",
            type=DimensionTypeChoices.LIST,
            parent=dim2,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Try to set dim1's parent to dim3 (would create circular reference)
        serializer = serializers.DimensionSerializer(
            dim1,
            data={'parent': dim3.id},
            partial=True,
            context={'workspace': self.workspace1}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)
        self.assertIn('circular', str(serializer.errors['parent']).lower())

    def test_valid_parent_hierarchy_accepted(self):
        """Test that valid parent hierarchy is accepted."""
        # Create dimension hierarchy: dim1 -> dim2 -> dim3
        dim1 = models.Dimension.objects.create(
            name="Dim1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        dim2 = models.Dimension.objects.create(
            name="Dim2",
            type=DimensionTypeChoices.LIST,
            parent=dim1,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Create a new dimension with dim2 as parent (valid hierarchy)
        serializer = serializers.DimensionSerializer(
            data={
                'name': 'Dim3',
                'type': DimensionTypeChoices.LIST,
                'parent': dim2.id,
                'workspace': self.workspace1.id
            },
            context={'workspace': self.workspace1}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_workspace_context_required(self):
        """Test that workspace context is required for validation."""
        serializer = serializers.DimensionSerializer(
            data={
                'name': 'Test Dimension',
                'type': DimensionTypeChoices.LIST
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('workspace', str(serializer.errors).lower())


class DimensionModelValidationTestCase(TestCase):
    """Test dimension validation at model layer."""

    def setUp(self):
        """Set up test fixtures."""
        self.workspace1 = models.Workspace.objects.create(
            name="Workspace 1",
            slug="workspace-1"
        )
        self.workspace2 = models.Workspace.objects.create(
            name="Workspace 2",
            slug="workspace-2"
        )

        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_model_validates_parent_workspace(self):
        """Test that model validates parent workspace match."""
        parent_ws2 = models.Dimension.objects.create(
            name="Parent WS2",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

        # Try to create dimension in workspace1 with parent from workspace2
        with self.assertRaises(DjangoValidationError) as context:
            dimension = models.Dimension(
                name="Child WS1",
                type=DimensionTypeChoices.LIST,
                parent=parent_ws2,
                workspace=self.workspace1,
                created_by=self.user
            )
            dimension.save()

        self.assertIn('parent', str(context.exception).lower())
        self.assertIn('workspace', str(context.exception).lower())

    def test_model_validates_circular_reference(self):
        """Test that model validates circular references."""
        dim1 = models.Dimension.objects.create(
            name="Dim1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        dim2 = models.Dimension.objects.create(
            name="Dim2",
            type=DimensionTypeChoices.LIST,
            parent=dim1,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Try to create circular reference
        with self.assertRaises(DjangoValidationError) as context:
            dim1.parent = dim2
            dim1.save()

        self.assertIn('circular', str(context.exception).lower())


class DimensionAPIValidationTestCase(APITestCase):
    """Test dimension validation through API endpoints."""

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
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace2,
            role='admin'
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Create parent dimension in workspace 2
        self.parent_ws2 = models.Dimension.objects.create(
            name="Parent WS2",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace2,
            created_by=self.user
        )

    def test_api_rejects_parent_from_different_workspace(self):
        """Test that API rejects parent from different workspace."""
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimensions/'
        data = {
            'name': 'Child WS1',
            'type': DimensionTypeChoices.LIST,
            'parent': self.parent_ws2.id,
            'workspace': self.workspace1.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)

    def test_api_rejects_circular_reference(self):
        """Test that API rejects circular reference."""
        # Create dimension hierarchy
        dim1 = models.Dimension.objects.create(
            name="Dim1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        dim2 = models.Dimension.objects.create(
            name="Dim2",
            type=DimensionTypeChoices.LIST,
            parent=dim1,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Try to update dim1 to have dim2 as parent
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimensions/{dim1.id}/'
        data = {
            'parent': dim2.id
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent', response.data)
        self.assertIn('circular', str(response.data['parent']).lower())

    def test_api_accepts_valid_parent_hierarchy(self):
        """Test that API accepts valid parent hierarchy."""
        # Create parent dimension
        parent = models.Dimension.objects.create(
            name="Parent",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Create child dimension via API
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimensions/'
        data = {
            'name': 'Child',
            'type': DimensionTypeChoices.LIST,
            'parent': parent.id,
            'workspace': self.workspace1.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent.id)

    def test_api_update_parent_relationship(self):
        """Test updating parent relationship through API."""
        # Create two parent dimensions
        parent1 = models.Dimension.objects.create(
            name="Parent1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )
        parent2 = models.Dimension.objects.create(
            name="Parent2",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Create child with parent1
        child = models.Dimension.objects.create(
            name="Child",
            type=DimensionTypeChoices.LIST,
            parent=parent1,
            workspace=self.workspace1,
            created_by=self.user
        )

        # Update to parent2
        url = f'/api/v1/workspaces/{self.workspace1.id}/dimensions/{child.id}/'
        data = {
            'parent': parent2.id
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['parent'], parent2.id)

        # Verify in database
        child.refresh_from_db()
        self.assertEqual(child.parent, parent2)


class DimensionValidationEdgeCasesTestCase(TestCase):
    """Test edge cases in dimension validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.workspace = models.Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace"
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_dimension_without_parent_is_valid(self):
        """Test that dimension without parent is valid."""
        serializer = serializers.DimensionSerializer(
            data={
                'name': 'Root Dimension',
                'type': DimensionTypeChoices.LIST,
                'workspace': self.workspace.id
            },
            context={'workspace': self.workspace}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_changing_parent_to_none_is_valid(self):
        """Test that changing parent to None is valid."""
        parent = models.Dimension.objects.create(
            name="Parent",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user
        )
        child = models.Dimension.objects.create(
            name="Child",
            type=DimensionTypeChoices.LIST,
            parent=parent,
            workspace=self.workspace,
            created_by=self.user
        )

        # Remove parent
        serializer = serializers.DimensionSerializer(
            child,
            data={'parent': None},
            partial=True,
            context={'workspace': self.workspace}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_deep_hierarchy_is_valid(self):
        """Test that deep parent hierarchy is valid (no circular reference)."""
        # Create 5-level hierarchy
        dim1 = models.Dimension.objects.create(
            name="Level1",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user
        )
        dim2 = models.Dimension.objects.create(
            name="Level2",
            type=DimensionTypeChoices.LIST,
            parent=dim1,
            workspace=self.workspace,
            created_by=self.user
        )
        dim3 = models.Dimension.objects.create(
            name="Level3",
            type=DimensionTypeChoices.LIST,
            parent=dim2,
            workspace=self.workspace,
            created_by=self.user
        )
        dim4 = models.Dimension.objects.create(
            name="Level4",
            type=DimensionTypeChoices.LIST,
            parent=dim3,
            workspace=self.workspace,
            created_by=self.user
        )

        # Add 5th level
        serializer = serializers.DimensionSerializer(
            data={
                'name': 'Level5',
                'type': DimensionTypeChoices.LIST,
                'parent': dim4.id,
                'workspace': self.workspace.id
            },
            context={'workspace': self.workspace}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
