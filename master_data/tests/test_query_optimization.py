"""
Tests for query optimization in ViewSets and Serializers.

These tests verify that N+1 query problems are properly addressed
using select_related, prefetch_related, and annotations.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from master_data import models
from master_data.constants import DimensionTypeChoices
from users.models import WorkspaceUser

User = get_user_model()


class QueryOptimizationTestCase(APITestCase):
    """Test query optimization across all major ViewSets."""

    def setUp(self):
        """Set up test fixtures with realistic data."""
        self.client = APIClient()

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

        # Assign user to workspace
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='admin'
        )

        # Authenticate
        self.client.force_authenticate(user=self.user)

        # Create platform
        self.platform = models.Platform.objects.create(
            name="Snowflake",
            slug="snowflake"
        )

        # Create fields (Fields are workspace-agnostic)
        self.field1 = models.Field.objects.create(
            name="Database",
            field_level=1,
            platform=self.platform
        )
        self.field2 = models.Field.objects.create(
            name="Schema",
            field_level=2,
            platform=self.platform
        )
        self.field1.next_field = self.field2
        self.field1.save()

        # Create dimensions with parent relationships
        self.dim_environment = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user
        )
        self.dim_project = models.Dimension.objects.create(
            name="Project",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user,
            parent=self.dim_environment
        )

        # Create dimension values
        for i in range(10):
            models.DimensionValue.objects.create(
                dimension=self.dim_environment,
                value=f"env{i}",
                label=f"Environment {i}",
                utm=f"env{i}",
                workspace=self.workspace,
                created_by=self.user
            )

        for i in range(10):
            models.DimensionValue.objects.create(
                dimension=self.dim_project,
                value=f"proj{i}",
                label=f"Project {i}",
                utm=f"proj{i}",
                workspace=self.workspace,
                created_by=self.user
            )

        # Create rule
        self.rule = models.Rule.objects.create(
            name="Test Rule",
            platform=self.platform,
            workspace=self.workspace,
            created_by=self.user
        )

        # Create rule details
        for field in [self.field1, self.field2]:
            for dimension in [self.dim_environment, self.dim_project]:
                models.RuleDetail.objects.create(
                    rule=self.rule,
                    field=field,
                    dimension=dimension,
                    dimension_order=1 if dimension == self.dim_environment else 2,
                    workspace=self.workspace,
                    created_by=self.user
                )

        # Create submission (requires rule and starting_field)
        self.submission = models.Submission.objects.create(
            name="Test Submission",
            rule=self.rule,
            starting_field=self.field1,
            workspace=self.workspace,
            created_by=self.user
        )

        # Create strings
        for i in range(50):
            string_obj = models.String.objects.create(
                submission=self.submission,
                field=self.field1,
                rule=self.rule,
                value=f"test_string_{i}",
                workspace=self.workspace,
                created_by=self.user
            )
            # Create string details
            models.StringDetail.objects.create(
                string=string_obj,
                dimension=self.dim_environment,
                dimension_value=models.DimensionValue.objects.filter(
                    dimension=self.dim_environment
                ).first(),
                workspace=self.workspace
            )

    def test_string_list_query_count(self):
        """Test that string list endpoint uses optimal number of queries."""
        url = f'/api/v1/workspaces/{self.workspace.id}/strings/'

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 50)

        # Should use ~5-7 queries:
        # 1. Authentication/session
        # 2. Workspace validation
        # 3. String list with select_related (single query with JOINs)
        # 4. Prefetch string_details
        # 5. Maybe a few more for workspace checks
        query_count = len(context.captured_queries)
        self.assertLess(
            query_count, 15,
            f"Too many queries for string list: {query_count}\n"
            f"Queries: {[q['sql'] for q in context.captured_queries]}"
        )

    def test_dimension_list_query_count(self):
        """Test that dimension list endpoint uses optimal number of queries."""
        url = f'/api/v1/workspaces/{self.workspace.id}/dimensions/'

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use ~5-7 queries:
        # 1. Authentication/session
        # 2. Workspace validation
        # 3. Dimension list with select_related (single query with JOINs)
        # 4. Prefetch dimension_values
        # 5. Maybe a few more for workspace checks
        query_count = len(context.captured_queries)
        self.assertLess(
            query_count, 15,
            f"Too many queries for dimension list: {query_count}\n"
            f"Queries: {[q['sql'] for q in context.captured_queries]}"
        )

    def test_rule_list_query_count(self):
        """Test that rule list endpoint uses optimal number of queries."""
        url = f'/api/v1/workspaces/{self.workspace.id}/rules/'

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use ~7-10 queries:
        # 1. Authentication/session
        # 2. Workspace validation
        # 3. Rule list with select_related
        # 4-8. Prefetch rule_details and nested relationships
        query_count = len(context.captured_queries)
        self.assertLess(
            query_count, 20,
            f"Too many queries for rule list: {query_count}\n"
            f"Queries: {[q['sql'] for q in context.captured_queries]}"
        )

    def test_rule_detail_list_query_count(self):
        """Test that rule detail list endpoint uses optimal number of queries."""
        url = f'/api/v1/workspaces/{self.workspace.id}/rule-details/'

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use ~7-10 queries:
        # 1. Authentication/session
        # 2. Workspace validation
        # 3. Rule detail list with select_related and annotation
        # 4. Maybe a few more for workspace checks
        query_count = len(context.captured_queries)
        self.assertLess(
            query_count, 15,
            f"Too many queries for rule detail list: {query_count}\n"
            f"Queries: {[q['sql'] for q in context.captured_queries]}"
        )

    def test_rule_retrieve_query_count(self):
        """Test that rule retrieve endpoint uses optimal number of queries."""
        url = f'/api/v1/workspaces/{self.workspace.id}/rules/{self.rule.id}/'

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use ~10-15 queries for retrieve with nested data
        query_count = len(context.captured_queries)
        self.assertLess(
            query_count, 25,
            f"Too many queries for rule retrieve: {query_count}\n"
            f"Queries: {[q['sql'] for q in context.captured_queries]}"
        )

    def test_string_retrieve_query_count(self):
        """Test that string retrieve endpoint uses optimal number of queries."""
        string_obj = models.String.objects.first()
        url = f'/api/v1/workspaces/{self.workspace.id}/strings/{string_obj.id}/'

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use ~7-10 queries for retrieve
        query_count = len(context.captured_queries)
        self.assertLess(
            query_count, 15,
            f"Too many queries for string retrieve: {query_count}\n"
            f"Queries: {[q['sql'] for q in context.captured_queries]}"
        )

    def test_dimension_value_list_query_count(self):
        """Test that dimension value list endpoint uses optimal number of queries."""
        url = f'/api/v1/workspaces/{self.workspace.id}/dimension-values/'

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should use ~7-10 queries
        query_count = len(context.captured_queries)
        self.assertLess(
            query_count, 15,
            f"Too many queries for dimension value list: {query_count}\n"
            f"Queries: {[q['sql'] for q in context.captured_queries]}"
        )


class AnnotationTestCase(TestCase):
    """Test that annotations are properly applied."""

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

        self.platform = models.Platform.objects.create(
            name="Snowflake",
            slug="snowflake"
        )

        self.field1 = models.Field.objects.create(
            name="Database",
            field_level=1,
            platform=self.platform
        )
        self.field2 = models.Field.objects.create(
            name="Schema",
            field_level=2,
            platform=self.platform
        )

        self.dimension = models.Dimension.objects.create(
            name="Environment",
            type=DimensionTypeChoices.LIST,
            workspace=self.workspace,
            created_by=self.user
        )

        self.rule = models.Rule.objects.create(
            name="Test Rule",
            platform=self.platform,
            workspace=self.workspace,
            created_by=self.user
        )

        # Create rule detail for field1
        self.rule_detail1 = models.RuleDetail.objects.create(
            rule=self.rule,
            field=self.field1,
            dimension=self.dimension,
            dimension_order=1,
            workspace=self.workspace,
            created_by=self.user
        )

        # Create rule detail for field2 (should inherit from field1)
        self.rule_detail2 = models.RuleDetail.objects.create(
            rule=self.rule,
            field=self.field2,
            dimension=self.dimension,
            dimension_order=1,
            workspace=self.workspace,
            created_by=self.user
        )

    def test_in_parent_field_annotation(self):
        """Test that in_parent_field annotation is correctly applied."""
        from django.db.models import Exists, OuterRef

        # Build queryset with annotation (simulating RuleDetailViewSet)
        parent_field_subquery = models.RuleDetail.objects.filter(
            rule=OuterRef('rule'),
            field__platform=OuterRef('field__platform'),
            dimension=OuterRef('dimension'),
            field__field_level=OuterRef('field__field_level') - 1
        )

        queryset = models.RuleDetail.objects.filter(
            workspace=self.workspace
        ).annotate(
            in_parent_field=Exists(parent_field_subquery)
        ).select_related('field', 'dimension', 'rule')

        # Get rule details
        rule_details = list(queryset.order_by('field__field_level'))

        # rule_detail1 (field_level=1) should NOT have parent field
        self.assertFalse(
            rule_details[0].in_parent_field,
            "Field level 1 should not have parent field"
        )

        # rule_detail2 (field_level=2) SHOULD have parent field
        self.assertTrue(
            rule_details[1].in_parent_field,
            "Field level 2 should have parent field"
        )

    def test_annotation_prevents_queries(self):
        """Test that using annotation prevents additional queries."""
        from django.db.models import Exists, OuterRef

        parent_field_subquery = models.RuleDetail.objects.filter(
            rule=OuterRef('rule'),
            field__platform=OuterRef('field__platform'),
            dimension=OuterRef('dimension'),
            field__field_level=OuterRef('field__field_level') - 1
        )

        queryset = models.RuleDetail.objects.filter(
            workspace=self.workspace
        ).annotate(
            in_parent_field=Exists(parent_field_subquery)
        ).select_related('field', 'dimension', 'rule')

        # Force evaluation
        rule_details = list(queryset)

        # Now accessing in_parent_field should not trigger any queries
        with CaptureQueriesContext(connection) as context:
            for detail in rule_details:
                _ = detail.in_parent_field

        # Should be 0 queries since annotation is already loaded
        self.assertEqual(
            len(context.captured_queries), 0,
            f"Accessing annotation triggered queries: {context.captured_queries}"
        )
