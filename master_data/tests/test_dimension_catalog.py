from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Rule, RuleDetail, Dimension, DimensionValue, Field, Platform, Workspace
from ..services import DimensionCatalogService

User = get_user_model()


class DimensionCatalogServiceTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass'
        )

        # Create workspace
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace',
            created_by=self.user
        )

        # Create platform
        self.platform = Platform.objects.create(
            name='Test Platform',
            slug='test-platform',
            platform_type='test',
            created_by=self.user
        )

        # Create rule
        self.rule = Rule.objects.create(
            name='Test Rule',
            slug='test-rule',
            platform=self.platform,
            workspace=self.workspace,
            created_by=self.user
        )

        # Create field
        self.field = Field.objects.create(
            name='Test Field',
            field_level=1,
            platform=self.platform,
            created_by=self.user
        )

        # Create dimension
        self.dimension = Dimension.objects.create(
            name='Test Dimension',
            slug='test-dimension',
            type='text',
            workspace=self.workspace,
            created_by=self.user
        )

        # Create rule detail
        self.rule_detail = RuleDetail.objects.create(
            rule=self.rule,
            field=self.field,
            dimension=self.dimension,
            dimension_order=1,
            workspace=self.workspace,
            created_by=self.user
        )

        # Create dimension value
        self.dimension_value = DimensionValue.objects.create(
            dimension=self.dimension,
            value='test value',
            label='Test Value',
            workspace=self.workspace,
            created_by=self.user
        )

        self.service = DimensionCatalogService()

    def test_get_optimized_catalog_for_rule(self):
        """Test that get_optimized_catalog_for_rule returns the expected structure"""
        catalog = self.service.get_optimized_catalog_for_rule(self.rule.id)

        # Check basic structure
        self.assertEqual(catalog['rule'], self.rule.id)
        self.assertEqual(catalog['rule_name'], self.rule.name)
        self.assertEqual(catalog['rule_slug'], self.rule.slug)

        # Check dimensions
        self.assertIn(self.dimension.id, catalog['dimensions'])
        dimension_data = catalog['dimensions'][self.dimension.id]
        self.assertEqual(dimension_data['name'], self.dimension.name)
        self.assertEqual(dimension_data['type'], self.dimension.type)

        # Check dimension values
        self.assertIn(self.dimension.id, catalog['dimension_values'])
        value_data = catalog['dimension_values'][self.dimension.id][0]
        self.assertEqual(value_data['value'], self.dimension_value.value)
        self.assertEqual(value_data['label'], self.dimension_value.label)

        # Check metadata indexes
        self.assertIn('metadata_indexes', catalog)
        indexes = catalog['metadata_indexes']

        # Check fast lookups
        self.assertIn('fast_lookups', indexes)
        fast_lookups = indexes['fast_lookups']

        # Check by_dimension_id lookup
        self.assertIn('by_dimension_id', fast_lookups)
        dimension_lookup = fast_lookups['by_dimension_id']
        self.assertIn(self.dimension.id, dimension_lookup)

        # Check dimension lookup data
        dim_data = dimension_lookup[self.dimension.id]
        self.assertEqual(dim_data['name'], self.dimension.name)
        self.assertEqual(dim_data['type'], self.dimension.type)
        self.assertTrue(dim_data['allows_freetext'])  # Since type is 'text'
        self.assertFalse(dim_data['is_dropdown'])  # Since type is 'text'
