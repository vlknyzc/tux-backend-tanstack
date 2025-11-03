"""
Tests for thread-local storage cleanup in WorkspaceMiddleware (Issue #23).

These tests verify that thread-local data is properly cleaned up between requests
to prevent data leakage between requests served by the same thread.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from unittest import mock
import logging

from main.middleware import WorkspaceMiddleware
from master_data.models.base import _thread_locals
from master_data import models

User = get_user_model()


class ThreadLocalCleanupTestCase(TestCase):
    """Test thread-local storage cleanup in middleware."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.middleware = WorkspaceMiddleware(get_response=lambda r: HttpResponse("OK"))

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create test workspace
        self.workspace = models.Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace"
        )

        # Ensure thread-locals start clean
        _thread_locals.__dict__.clear()

    def tearDown(self):
        """Clean up after each test."""
        _thread_locals.__dict__.clear()

    def test_thread_local_cleanup_after_request(self):
        """Test that thread-local data is cleaned up after successful request."""
        # Create request
        request = self.factory.get('/api/v1/workspaces/')
        request.user = self.user

        # Process request - should set thread-local data
        self.middleware.process_request(request)

        # Verify thread-local data was set
        self.assertTrue(hasattr(_thread_locals, 'request_id'))
        self.assertTrue(hasattr(_thread_locals, 'is_superuser'))
        request_id = _thread_locals.request_id

        # Process response - should clear thread-local data
        response = HttpResponse("OK")
        self.middleware.process_response(request, response)

        # Verify thread-local data was cleared
        self.assertFalse(hasattr(_thread_locals, 'request_id'))
        self.assertFalse(hasattr(_thread_locals, 'is_superuser'))
        self.assertFalse(hasattr(_thread_locals, 'workspace_id'))

    def test_thread_local_cleanup_on_exception(self):
        """Test that thread-local data is cleaned up when exception occurs."""
        # Create request
        request = self.factory.get('/api/v1/workspaces/')
        request.user = self.user

        # Process request - should set thread-local data
        self.middleware.process_request(request)

        # Verify thread-local data was set
        self.assertTrue(hasattr(_thread_locals, 'request_id'))

        # Simulate exception - should clean up thread-local data
        exception = Exception("Test exception")
        result = self.middleware.process_exception(request, exception)

        # process_exception should return None to let exception propagate
        self.assertIsNone(result)

        # Verify thread-local data was cleared
        self.assertFalse(hasattr(_thread_locals, 'request_id'))
        self.assertFalse(hasattr(_thread_locals, 'is_superuser'))
        self.assertFalse(hasattr(_thread_locals, 'workspace_id'))

    def test_stale_data_detection(self):
        """Test that stale thread-local data from previous request is detected."""
        # Manually set stale thread-local data (simulating failed cleanup)
        _thread_locals.request_id = "stale-request-id"
        _thread_locals.workspace_id = 123
        _thread_locals.is_superuser = True

        # Create new request
        request = self.factory.get('/api/v1/workspaces/')
        request.user = self.user

        # Process request - should detect and clear stale data
        with self.assertLogs('main.middleware', level='WARNING') as log_context:
            self.middleware.process_request(request)

            # Verify warning was logged about stale data
            self.assertTrue(
                any('Thread-local data not cleaned from previous request' in msg
                    for msg in log_context.output)
            )

        # Verify new request ID was set (not the stale one)
        self.assertTrue(hasattr(_thread_locals, 'request_id'))
        self.assertNotEqual(_thread_locals.request_id, "stale-request-id")
        self.assertEqual(_thread_locals.request_id, request.request_id)

    def test_request_id_uniqueness(self):
        """Test that each request gets a unique request ID."""
        # Request 1
        request1 = self.factory.get('/api/v1/workspaces/')
        request1.user = self.user
        self.middleware.process_request(request1)
        request_id_1 = request1.request_id

        response1 = HttpResponse("OK")
        self.middleware.process_response(request1, response1)

        # Request 2
        request2 = self.factory.get('/api/v1/workspaces/')
        request2.user = self.user
        self.middleware.process_request(request2)
        request_id_2 = request2.request_id

        # Verify unique IDs
        self.assertNotEqual(request_id_1, request_id_2)

    def test_request_id_mismatch_detection(self):
        """Test detection of request ID mismatch during cleanup."""
        # Create request 1
        request1 = self.factory.get('/api/v1/workspaces/')
        request1.user = self.user
        self.middleware.process_request(request1)

        # Manually change thread-local request_id to simulate mismatch
        _thread_locals.request_id = "mismatched-id"

        # Process response - should detect mismatch
        response = HttpResponse("OK")
        with self.assertLogs('main.middleware', level='ERROR') as log_context:
            self.middleware.process_response(request1, response)

            # Verify error was logged about mismatch
            self.assertTrue(
                any('Thread-local request ID mismatch' in msg
                    for msg in log_context.output)
            )

        # Verify cleanup still happened despite mismatch
        self.assertFalse(hasattr(_thread_locals, 'request_id'))

    def test_workspace_context_isolation(self):
        """Test that workspace context doesn't leak between requests."""
        # Request 1 - set workspace context
        request1 = self.factory.get('/api/v1/workspaces/')
        request1.user = self.user
        self.middleware.process_request(request1)
        _thread_locals.workspace_id = 123  # Simulate workspace being set by view

        # Cleanup after request 1
        response1 = HttpResponse("OK")
        self.middleware.process_response(request1, response1)

        # Request 2 - should not see workspace from request 1
        request2 = self.factory.get('/api/v1/workspaces/')
        request2.user = self.user
        self.middleware.process_request(request2)

        # Verify workspace_id is not set (None by default)
        workspace_id = getattr(_thread_locals, 'workspace_id', 'NOT_SET')
        self.assertEqual(workspace_id, None)  # Should be None, not 123

    def test_superuser_context_isolation(self):
        """Test that superuser context doesn't leak between requests."""
        # Request 1 - superuser
        superuser = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            is_superuser=True
        )
        request1 = self.factory.get('/api/v1/workspaces/')
        request1.user = superuser
        self.middleware.process_request(request1)

        # Verify superuser flag is set
        self.assertTrue(_thread_locals.is_superuser)

        # Cleanup after request 1
        response1 = HttpResponse("OK")
        self.middleware.process_response(request1, response1)

        # Request 2 - regular user
        request2 = self.factory.get('/api/v1/workspaces/')
        request2.user = self.user
        self.middleware.process_request(request2)

        # Verify superuser flag is False (not leaked from request 1)
        self.assertFalse(_thread_locals.is_superuser)

    def test_cleanup_robustness(self):
        """Test that cleanup works even with unusual thread-local state."""
        # Create request
        request = self.factory.get('/api/v1/workspaces/')
        request.user = self.user
        self.middleware.process_request(request)

        # Add some custom attributes to thread-locals
        _thread_locals.custom_attr_1 = "value1"
        _thread_locals.custom_attr_2 = "value2"
        _thread_locals.custom_dict = {"key": "value"}

        # Process response - should clear ALL attributes
        response = HttpResponse("OK")
        self.middleware.process_response(request, response)

        # Verify all thread-local data was cleared
        self.assertFalse(hasattr(_thread_locals, 'request_id'))
        self.assertFalse(hasattr(_thread_locals, 'is_superuser'))
        self.assertFalse(hasattr(_thread_locals, 'workspace_id'))
        self.assertFalse(hasattr(_thread_locals, 'custom_attr_1'))
        self.assertFalse(hasattr(_thread_locals, 'custom_attr_2'))
        self.assertFalse(hasattr(_thread_locals, 'custom_dict'))

        # Verify __dict__ is empty
        self.assertEqual(len(_thread_locals.__dict__), 0)

    def test_unauthenticated_request(self):
        """Test thread-local cleanup with unauthenticated request."""
        # Create unauthenticated request
        request = self.factory.get('/api/v1/workspaces/')
        # No user attribute

        # Process request
        self.middleware.process_request(request)

        # Verify is_superuser is set to False for unauthenticated
        self.assertFalse(_thread_locals.is_superuser)

        # Cleanup
        response = HttpResponse("OK")
        self.middleware.process_response(request, response)

        # Verify cleanup happened
        self.assertFalse(hasattr(_thread_locals, 'request_id'))
        self.assertFalse(hasattr(_thread_locals, 'is_superuser'))

    def test_multiple_sequential_requests(self):
        """Test cleanup works correctly for multiple sequential requests."""
        # Request 1
        request1 = self.factory.get('/api/v1/workspaces/1/')
        request1.user = self.user
        self.middleware.process_request(request1)
        _thread_locals.workspace_id = 1
        request_id_1 = request1.request_id

        response1 = HttpResponse("OK")
        self.middleware.process_response(request1, response1)

        # Verify cleanup
        self.assertFalse(hasattr(_thread_locals, 'request_id'))

        # Request 2
        request2 = self.factory.get('/api/v1/workspaces/2/')
        request2.user = self.user
        self.middleware.process_request(request2)
        _thread_locals.workspace_id = 2
        request_id_2 = request2.request_id

        # Verify new request has different ID
        self.assertNotEqual(request_id_1, request_id_2)

        response2 = HttpResponse("OK")
        self.middleware.process_response(request2, response2)

        # Verify cleanup
        self.assertFalse(hasattr(_thread_locals, 'request_id'))

        # Request 3
        request3 = self.factory.get('/api/v1/workspaces/3/')
        request3.user = self.user
        self.middleware.process_request(request3)
        _thread_locals.workspace_id = 3

        # Verify workspace from request 1 and 2 not present
        self.assertNotEqual(_thread_locals.workspace_id, 1)
        self.assertNotEqual(_thread_locals.workspace_id, 2)
        self.assertEqual(_thread_locals.workspace_id, 3)


class ThreadLocalCleanupIntegrationTestCase(TestCase):
    """Integration tests for thread-local cleanup using Django test client."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create test workspace
        self.workspace = models.Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace"
        )

        # Assign user to workspace
        from users.models import WorkspaceUser
        WorkspaceUser.objects.create(
            user=self.user,
            workspace=self.workspace,
            role='admin'
        )

        # Ensure thread-locals start clean
        _thread_locals.__dict__.clear()

    def tearDown(self):
        """Clean up after each test."""
        _thread_locals.__dict__.clear()

    def test_api_request_cleanup(self):
        """Test thread-local cleanup with actual API request."""
        # Authenticate
        self.client.force_login(self.user)

        # Make API request
        response = self.client.get(f'/api/v1/workspaces/{self.workspace.id}/')

        # After request completes, thread-locals should be cleaned
        # Note: This test is tricky because Django test client may use different thread
        # But the middleware should still clean up after each request
        self.assertEqual(response.status_code, 200)

        # Make another request to different workspace
        workspace2 = models.Workspace.objects.create(
            name="Test Workspace 2",
            slug="test-workspace-2"
        )

        response2 = self.client.get(f'/api/v1/workspaces/{workspace2.id}/')

        # Should not see data from previous request
        # If cleanup failed, this test would fail due to workspace isolation issues
        # The 404 is expected because user is not assigned to workspace2
        self.assertEqual(response2.status_code, 404)
