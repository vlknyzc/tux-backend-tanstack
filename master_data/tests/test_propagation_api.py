"""
Tests for propagation API endpoints.
"""

import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from master_data.models import (
    Workspace, Platform, Field, Rule, RuleDetail,
    Dimension, DimensionValue, Submission, String, StringDetail,
    PropagationJob, PropagationError, PropagationSettings
)

User = get_user_model()


class PropagationAPITestCase(TestCase):
    """Test case for propagation API endpoints."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

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

        # Create dimension
        self.dimension = Dimension.objects.create(
            workspace=self.workspace,
            name='Brand',
            dimension_type='list'
        )

        # Create dimension values
        self.brand_nike = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension,
            value='Nike',
            label='Nike Brand'
        )
        self.brand_adidas = DimensionValue.objects.create(
            workspace=self.workspace,
            dimension=self.dimension,
            value='Adidas',
            label='Adidas Brand'
        )

        # Create rule
        self.rule = Rule.objects.create(
            workspace=self.workspace,
            platform=self.platform,
            name='Test Rule'
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
            value='Nike-Test',
            is_auto_generated=True
        )

        # Create string detail
        self.string_detail = StringDetail.objects.create(
            workspace=self.workspace,
            string=self.string,
            dimension=self.dimension,
            dimension_value=self.brand_nike
        )

        # Mock workspace context middleware
        self.client.defaults['HTTP_X_WORKSPACE_ID'] = str(self.workspace.id)

    def test_analyze_impact_endpoint(self):
        """Test the impact analysis endpoint."""
        url = reverse('enhanced-stringdetail-analyze-impact')
        data = {
            'string_detail_updates': [
                {
                    'string_detail_id': self.string_detail.id,
                    'dimension_value': self.brand_adidas.id
                }
            ],
            'max_depth': 5
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('affected_strings', response_data)
        self.assertIn('warnings', response_data)
        self.assertIn('conflicts', response_data)
        self.assertIn('summary', response_data)

    def test_analyze_impact_invalid_data(self):
        """Test impact analysis with invalid data."""
        url = reverse('enhanced-stringdetail-analyze-impact')
        data = {
            'string_detail_updates': [],  # Empty list
            'max_depth': 5
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analyze_impact_missing_string_detail_id(self):
        """Test impact analysis with missing string_detail_id."""
        url = reverse('enhanced-stringdetail-analyze-impact')
        data = {
            'string_detail_updates': [
                {
                    'dimension_value': self.brand_adidas.id
                    # Missing string_detail_id
                }
            ],
            'max_depth': 5
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enhanced_string_detail_update_dry_run(self):
        """Test enhanced string detail update with dry run."""
        url = reverse('enhanced-stringdetail-detail', kwargs={'pk': self.string_detail.id})
        data = {
            'dimension_value': self.brand_adidas.id,
            'dry_run': True,
            'propagate': True,
            'propagation_depth': 5
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertTrue(response_data['dry_run'])
        self.assertIn('impact_analysis', response_data)
        
        # Verify original data wasn't changed
        self.string_detail.refresh_from_db()
        self.assertEqual(self.string_detail.dimension_value, self.brand_nike)

    def test_enhanced_string_detail_update_actual(self):
        """Test actual enhanced string detail update."""
        url = reverse('enhanced-stringdetail-detail', kwargs={'pk': self.string_detail.id})
        data = {
            'dimension_value': self.brand_adidas.id,
            'dry_run': False,
            'propagate': True,
            'propagation_depth': 5
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('propagation_summary', response_data)
        
        # Verify data was actually changed
        self.string_detail.refresh_from_db()
        self.assertEqual(self.string_detail.dimension_value, self.brand_adidas)

    def test_batch_update_endpoint(self):
        """Test batch update endpoint."""
        url = reverse('enhanced-stringdetail-batch-update')
        data = {
            'updates': [
                {
                    'string_detail_id': self.string_detail.id,
                    'dimension_value': self.brand_adidas.id
                }
            ],
            'options': {
                'propagate': True,
                'max_depth': 5,
                'error_handling': 'continue'
            }
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('job_id', response_data)
        self.assertIn('successful_updates', response_data)
        self.assertIn('total_affected', response_data)

    def test_batch_update_too_many_updates(self):
        """Test batch update with too many updates."""
        url = reverse('enhanced-stringdetail-batch-update')
        
        # Create 101 updates (over the limit)
        updates = []
        for i in range(101):
            updates.append({
                'string_detail_id': self.string_detail.id,
                'dimension_value': self.brand_adidas.id
            })
        
        data = {
            'updates': updates,
            'options': {}
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_propagation_job_list(self):
        """Test listing propagation jobs."""
        # Create a test job
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            triggered_by=self.user,
            status='completed',
            total_strings=10,
            processed_strings=10
        )

        url = reverse('propagation-job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('results', response_data)
        self.assertEqual(len(response_data['results']), 1)
        self.assertEqual(response_data['results'][0]['id'], job.id)

    def test_propagation_job_detail(self):
        """Test retrieving propagation job details."""
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            triggered_by=self.user,
            status='completed',
            total_strings=10,
            processed_strings=10
        )

        url = reverse('propagation-job-detail', kwargs={'pk': job.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data['id'], job.id)
        self.assertEqual(response_data['status'], 'completed')
        self.assertIn('triggered_by_name', response_data)

    def test_propagation_job_errors(self):
        """Test getting errors for a propagation job."""
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            triggered_by=self.user,
            status='failed'
        )
        
        error = PropagationError.objects.create(
            workspace=self.workspace,
            job=job,
            error_type='test_error',
            error_message='Test error message'
        )

        url = reverse('propagation-job-errors', kwargs={'pk': job.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['id'], error.id)

    def test_propagation_job_summary(self):
        """Test getting propagation job summary."""
        # Create some test jobs
        PropagationJob.objects.create(
            workspace=self.workspace,
            status='completed'
        )
        PropagationJob.objects.create(
            workspace=self.workspace,
            status='failed'
        )

        url = reverse('propagation-job-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('total_jobs', response_data)
        self.assertIn('completed_jobs', response_data)
        self.assertIn('failed_jobs', response_data)
        self.assertIn('success_rate', response_data)

    def test_propagation_error_list(self):
        """Test listing propagation errors."""
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            status='failed'
        )
        
        error = PropagationError.objects.create(
            workspace=self.workspace,
            job=job,
            error_type='test_error',
            error_message='Test error message'
        )

        url = reverse('propagation-error-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertIn('results', response_data)
        self.assertEqual(len(response_data['results']), 1)

    def test_propagation_error_mark_resolved(self):
        """Test marking a propagation error as resolved."""
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            status='failed'
        )
        
        error = PropagationError.objects.create(
            workspace=self.workspace,
            job=job,
            error_type='test_error',
            error_message='Test error message',
            resolved=False
        )

        url = reverse('propagation-error-mark-resolved', kwargs={'pk': error.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify error was marked as resolved
        error.refresh_from_db()
        self.assertTrue(error.resolved)
        self.assertEqual(error.resolved_by, self.user)

    def test_propagation_error_mark_resolved_already_resolved(self):
        """Test marking an already resolved error."""
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            status='failed'
        )
        
        error = PropagationError.objects.create(
            workspace=self.workspace,
            job=job,
            error_type='test_error',
            error_message='Test error message',
            resolved=True  # Already resolved
        )

        url = reverse('propagation-error-mark-resolved', kwargs={'pk': error.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_propagation_error_retry_not_retryable(self):
        """Test retrying a non-retryable error."""
        job = PropagationJob.objects.create(
            workspace=self.workspace,
            status='failed'
        )
        
        error = PropagationError.objects.create(
            workspace=self.workspace,
            job=job,
            error_type='test_error',
            error_message='Test error message',
            is_retryable=False
        )

        url = reverse('propagation-error-retry', kwargs={'pk': error.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_propagation_settings_current(self):
        """Test getting current user's propagation settings."""
        # Create settings for user
        settings = PropagationSettings.objects.create(
            user=self.user,
            workspace=self.workspace,
            settings={
                'default_propagation_enabled': True,
                'default_propagation_depth': 5
            }
        )

        url = reverse('propagation-settings-current')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.json()
        self.assertEqual(response_data['id'], settings.id)
        self.assertIn('settings', response_data)

    def test_propagation_settings_create(self):
        """Test creating propagation settings."""
        url = reverse('propagation-settings-list')
        data = {
            'settings': {
                'default_propagation_enabled': False,
                'default_propagation_depth': 3,
                'field_propagation_rules': {
                    'dimension_value': 'inherit_always'
                }
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify settings were created
        settings = PropagationSettings.objects.get(
            user=self.user,
            workspace=self.workspace
        )
        self.assertEqual(settings.settings['default_propagation_depth'], 3)

    def test_propagation_settings_update(self):
        """Test updating propagation settings."""
        settings = PropagationSettings.objects.create(
            user=self.user,
            workspace=self.workspace,
            settings={'default_propagation_enabled': True}
        )

        url = reverse('propagation-settings-detail', kwargs={'pk': settings.id})
        data = {
            'settings': {
                'default_propagation_enabled': False,
                'default_propagation_depth': 8
            }
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify settings were updated
        settings.refresh_from_db()
        self.assertFalse(settings.settings['default_propagation_enabled'])
        self.assertEqual(settings.settings['default_propagation_depth'], 8)

    def test_propagation_settings_invalid_depth(self):
        """Test creating settings with invalid propagation depth."""
        url = reverse('propagation-settings-list')
        data = {
            'settings': {
                'default_propagation_depth': 100  # Over limit
            }
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        self.client.force_authenticate(user=None)
        
        url = reverse('propagation-job-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_workspace_access_denied(self):
        """Test that users cannot access other workspaces' data."""
        # Create another workspace
        other_workspace = Workspace.objects.create(
            name='Other Workspace',
            status='active'
        )
        
        # Create job in other workspace
        job = PropagationJob.objects.create(
            workspace=other_workspace,
            status='completed'
        )

        # Try to access job from other workspace
        url = reverse('propagation-job-detail', kwargs={'pk': job.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)