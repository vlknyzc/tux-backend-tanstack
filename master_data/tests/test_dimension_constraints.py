"""
Tests for dimension constraint functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from ..models import (
    Workspace, Dimension, DimensionValue, DimensionConstraint,
    ConstraintTypeChoices
)
from ..services.constraint_validator import ConstraintValidatorService

User = get_user_model()


class DimensionConstraintModelTests(TestCase):
    """Tests for DimensionConstraint model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )
        self.dimension = Dimension.objects.create(
            name='Test Dimension',
            workspace=self.workspace,
            type='list',
            created_by=self.user
        )

    def test_create_constraint_no_value_required(self):
        """Test creating constraint that doesn't require a value."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1,
            created_by=self.user
        )
        self.assertEqual(constraint.dimension, self.dimension)
        self.assertEqual(constraint.constraint_type, ConstraintTypeChoices.LOWERCASE)
        self.assertTrue(constraint.is_active)

    def test_create_constraint_with_value(self):
        """Test creating constraint that requires a value."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.MAX_LENGTH,
            value='50',
            order=1,
            created_by=self.user
        )
        self.assertEqual(constraint.value, '50')

    def test_auto_order_assignment(self):
        """Test that order is automatically assigned."""
        constraint1 = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            created_by=self.user
        )
        constraint2 = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_SPACES,
            created_by=self.user
        )
        self.assertEqual(constraint1.order, 1)
        self.assertEqual(constraint2.order, 2)

    def test_get_default_error_message(self):
        """Test default error message generation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1
        )
        message = constraint.get_default_error_message()
        self.assertIn('lowercase', message.lower())


class ConstraintValidatorServiceTests(TestCase):
    """Tests for ConstraintValidatorService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )
        self.dimension = Dimension.objects.create(
            name='Test Dimension',
            workspace=self.workspace,
            type='list',
            created_by=self.user
        )

    def test_validate_no_spaces(self):
        """Test no_spaces constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_SPACES,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('test-value', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('test value', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_lowercase(self):
        """Test lowercase constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('testvalue', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('TestValue', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_uppercase(self):
        """Test uppercase constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.UPPERCASE,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('TESTVALUE', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('TestValue', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_no_special_chars(self):
        """Test no_special_chars constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_SPECIAL_CHARS,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('test_value123', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('test-value', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_alphanumeric(self):
        """Test alphanumeric constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.ALPHANUMERIC,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('test123', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('test_123', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_numeric(self):
        """Test numeric constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NUMERIC,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('12345', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('123a45', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_max_length(self):
        """Test max_length constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.MAX_LENGTH,
            value='5',
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('test', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('testvalue', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_min_length(self):
        """Test min_length constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.MIN_LENGTH,
            value='5',
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('testing', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('test', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_regex(self):
        """Test regex constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.REGEX,
            value=r'^[a-z0-9-]+$',
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('test-123', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('Test_123', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_starts_with(self):
        """Test starts_with constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.STARTS_WITH,
            value='utm_',
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('utm_campaign', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('campaign_utm', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_ends_with(self):
        """Test ends_with constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.ENDS_WITH,
            value='_prod',
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('env_prod', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('prod_env', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_allowed_chars(self):
        """Test allowed_chars constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.ALLOWED_CHARS,
            value='abc123',
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('abc123', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('abc123xyz', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_no_uppercase(self):
        """Test no_uppercase constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_UPPERCASE,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('test123', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('Test123', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_no_numbers(self):
        """Test no_numbers constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_NUMBERS,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('testvalue', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('test123', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_url_safe(self):
        """Test url_safe constraint validation."""
        constraint = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.URL_SAFE,
            order=1
        )

        # Valid
        result = ConstraintValidatorService.validate_constraint('test-value_123.txt', constraint)
        self.assertTrue(result.is_valid)

        # Invalid
        result = ConstraintValidatorService.validate_constraint('test value@123', constraint)
        self.assertFalse(result.is_valid)

    def test_validate_all_constraints(self):
        """Test validating against multiple constraints."""
        # Create multiple constraints
        DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1
        )
        DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_SPACES,
            order=2
        )
        DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.MAX_LENGTH,
            value='10',
            order=3
        )

        # Valid value
        result = ConstraintValidatorService.validate_all_constraints(
            'testvalue',
            self.dimension.id,
            use_cache=False
        )
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)

        # Invalid value (has space)
        result = ConstraintValidatorService.validate_all_constraints(
            'test value',
            self.dimension.id,
            use_cache=False
        )
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)

        # Invalid value (too long)
        result = ConstraintValidatorService.validate_all_constraints(
            'verylongvalue',
            self.dimension.id,
            use_cache=False
        )
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)


class DimensionConstraintAPITests(TestCase):
    """Tests for dimension constraint API endpoints."""

    def setUp(self):
        """Set up test data."""
        from users.models import WorkspaceUser

        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )

        # Grant user access to workspace
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='admin'
        )

        self.dimension = Dimension.objects.create(
            name='Test Dimension',
            workspace=self.workspace,
            type='list',
            created_by=self.user
        )

    def test_create_constraint(self):
        """Test creating a constraint via API."""
        url = '/api/v1/dimension-constraints/'
        data = {
            'dimension': self.dimension.id,
            'constraint_type': 'lowercase',
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['constraint_type'], 'lowercase')

    def test_list_constraints_by_dimension(self):
        """Test listing constraints for a dimension."""
        # Create constraints
        DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1
        )
        DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_SPACES,
            order=2
        )

        url = f'/api/v1/dimension-constraints/by-dimension/{self.dimension.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_bulk_create_constraints(self):
        """Test bulk creating constraints."""
        url = f'/api/v1/dimension-constraints/bulk-create/{self.dimension.id}/'
        data = {
            'constraints': [
                {'constraint_type': 'lowercase'},
                {'constraint_type': 'no_spaces'},
                {'constraint_type': 'max_length', 'value': '50'}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 3)

    def test_reorder_constraints(self):
        """Test reordering constraints."""
        # Create constraints
        c1 = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1
        )
        c2 = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.NO_SPACES,
            order=2
        )
        c3 = DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.MAX_LENGTH,
            value='50',
            order=3
        )

        url = f'/api/v1/dimension-constraints/reorder/{self.dimension.id}/'
        data = {'constraint_ids': [c3.id, c1.id, c2.id]}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify new order
        c1.refresh_from_db()
        c2.refresh_from_db()
        c3.refresh_from_db()
        self.assertEqual(c3.order, 1)
        self.assertEqual(c1.order, 2)
        self.assertEqual(c2.order, 3)

    def test_validate_value(self):
        """Test validating a value against constraints."""
        # Create constraint
        DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1
        )

        url = f'/api/v1/dimension-constraints/validate/{self.dimension.id}/'

        # Valid value
        response = self.client.post(url, {'value': 'testvalue'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])

        # Invalid value
        response = self.client.post(url, {'value': 'TestValue'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_valid'])


class DimensionValueConstraintIntegrationTests(TestCase):
    """Tests for dimension value constraint integration."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)

        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )
        self.dimension = Dimension.objects.create(
            name='Test Dimension',
            workspace=self.workspace,
            type='list',
            created_by=self.user
        )

        # Create constraint
        DimensionConstraint.objects.create(
            dimension=self.dimension,
            constraint_type=ConstraintTypeChoices.LOWERCASE,
            order=1
        )

    def test_create_dimension_value_with_valid_value(self):
        """Test creating dimension value with valid constraint."""
        url = '/api/v1/dimension-values/'
        data = {
            'dimension': self.dimension.id,
            'value': 'testvalue',
            'label': 'Test Value',
            'utm': 'test',
            'workspace': self.workspace.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_dimension_value_with_invalid_value(self):
        """Test creating dimension value with invalid constraint."""
        url = '/api/v1/dimension-values/'
        data = {
            'dimension': self.dimension.id,
            'value': 'TestValue',  # Uppercase - should fail
            'label': 'Test Value',
            'utm': 'test',
            'workspace': self.workspace.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('validation_errors', response.data)
