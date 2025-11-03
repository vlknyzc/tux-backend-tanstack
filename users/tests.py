"""
Tests for authentication rate limiting and security features.
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import time

User = get_user_model()


class RateLimitingTestCase(APITestCase):
    """Test rate limiting on authentication endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        # Use direct URL paths as they don't have URL names
        self.login_url = '/api/v1/jwt/create/'
        self.refresh_url = '/api/v1/jwt/refresh/'

        # Create a test user
        self.test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_login_rate_limiting(self):
        """Test that login endpoint is rate limited after 5 attempts."""
        # Make 5 failed login attempts (should succeed)
        for i in range(5):
            response = self.client.post(self.login_url, {
                'email': 'testuser@example.com',
                'password': 'wrongpassword'
            })
            # Should get 401 Unauthorized for wrong password
            self.assertIn(response.status_code, [401, 400])

        # 6th attempt should be rate limited (429 Too Many Requests)
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_account_lockout_after_failed_attempts(self):
        """Test that account is locked after 5 failed login attempts."""
        # Make 5 failed login attempts
        for i in range(5):
            response = self.client.post(self.login_url, {
                'email': 'testuser@example.com',
                'password': 'wrongpassword'
            })

        # Next attempt should return account locked message
        # (This might be rate limited or account locked, both are acceptable)
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123'  # Even with correct password
        })

        # Should either be rate limited or show validation error
        self.assertIn(response.status_code, [429, 400])

    def test_successful_login_clears_failed_attempts(self):
        """Test that successful login clears failed attempt counter."""
        # Make 2 failed attempts
        for i in range(2):
            self.client.post(self.login_url, {
                'email': 'testuser@example.com',
                'password': 'wrongpassword'
            })

        # Successful login
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Clear cache to reset throttling (simulating time passing)
        cache.clear()

        # Counter should be cleared, so 5 more failed attempts should be allowed
        for i in range(5):
            response = self.client.post(self.login_url, {
                'email': 'testuser@example.com',
                'password': 'wrongpassword'
            })
            # Should not be rate limited yet
            self.assertIn(response.status_code, [401, 400])

    def test_ip_based_rate_limiting(self):
        """Test that rate limiting works on IP address level."""
        # Try different emails from same IP
        for i in range(6):
            response = self.client.post(self.login_url, {
                'email': f'user{i}@example.com',
                'password': 'wrongpassword'
            })

            if i < 5:
                # First 5 attempts should fail with 401/400
                self.assertIn(response.status_code, [401, 400])
            else:
                # 6th attempt should be rate limited
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_token_refresh_rate_limiting(self):
        """Test that token refresh endpoint has rate limiting."""
        # First get a valid token
        login_response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        refresh_token = login_response.data.get('refresh')

        # Make 11 refresh attempts (limit is 10/minute)
        for i in range(11):
            response = self.client.post(self.refresh_url, {
                'refresh': refresh_token
            })

            if i < 10:
                # First 10 should succeed
                self.assertEqual(response.status_code, status.HTTP_200_OK)
            else:
                # 11th should be rate limited
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class FailedLoginTrackingTestCase(APITestCase):
    """Test failed login attempt tracking functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        # Use direct URL path as it doesn't have a URL name
        self.login_url = '/api/v1/jwt/create/'

        # Create a test user
        self.test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_failed_attempt_counter_increments(self):
        """Test that failed attempt counter increments correctly."""
        email_key = f'failed_login_{self.test_user.email}'

        # Make a failed login attempt
        self.client.post(self.login_url, {
            'email': self.test_user.email,
            'password': 'wrongpassword'
        })

        # Check that counter was incremented
        attempts = cache.get(email_key, 0)
        self.assertEqual(attempts, 1)

    def test_failed_attempt_counter_clears_on_success(self):
        """Test that failed attempt counter clears on successful login."""
        email_key = f'failed_login_{self.test_user.email}'

        # Make a failed attempt
        self.client.post(self.login_url, {
            'email': self.test_user.email,
            'password': 'wrongpassword'
        })

        # Verify counter is set
        self.assertGreater(cache.get(email_key, 0), 0)

        # Successful login
        self.client.post(self.login_url, {
            'email': self.test_user.email,
            'password': 'testpass123'
        })

        # Counter should be cleared
        attempts = cache.get(email_key, 0)
        self.assertEqual(attempts, 0)

    def test_account_lockout_message(self):
        """Test that account lockout returns appropriate message."""
        # Make 5 failed attempts to trigger lockout
        for i in range(5):
            self.client.post(self.login_url, {
                'email': self.test_user.email,
                'password': 'wrongpassword'
            })

        # Next attempt should return lockout message
        response = self.client.post(self.login_url, {
            'email': self.test_user.email,
            'password': 'testpass123'
        })

        # Should receive error response (400 or 429)
        self.assertIn(response.status_code, [400, 429])

        # Check that response contains lockout message
        if response.status_code == 400:
            response_data = str(response.data)
            self.assertIn('locked', response_data.lower())


class SecurityLoggingTestCase(APITestCase):
    """Test security logging functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        # Use direct URL path as it doesn't have a URL name
        self.login_url = '/api/v1/jwt/create/'

        # Create a test user
        self.test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_successful_login_is_logged(self):
        """Test that successful logins are logged."""
        # This test verifies the login succeeds (logging happens internally)
        response = self.client.post(self.login_url, {
            'email': self.test_user.email,
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_failed_login_is_logged(self):
        """Test that failed logins are logged."""
        # This test verifies the failed login is handled (logging happens internally)
        response = self.client.post(self.login_url, {
            'email': self.test_user.email,
            'password': 'wrongpassword'
        })

        self.assertIn(response.status_code, [401, 400])


class ThrottleClassesTestCase(TestCase):
    """Test custom throttle classes."""

    def test_authentication_throttle_rate(self):
        """Test that AuthenticationThrottle has correct rate."""
        from users.throttles import AuthenticationThrottle
        throttle = AuthenticationThrottle()
        self.assertEqual(throttle.rate, '5/minute')

    def test_token_refresh_throttle_rate(self):
        """Test that TokenRefreshThrottle has correct rate."""
        from users.throttles import TokenRefreshThrottle
        throttle = TokenRefreshThrottle()
        self.assertEqual(throttle.rate, '10/minute')

    def test_registration_throttle_rate(self):
        """Test that RegistrationThrottle has correct rate."""
        from users.throttles import RegistrationThrottle
        throttle = RegistrationThrottle()
        self.assertEqual(throttle.rate, '3/hour')

    def test_invitation_validation_throttle_rate(self):
        """Test that InvitationValidationThrottle has correct rate."""
        from users.throttles import InvitationValidationThrottle
        throttle = InvitationValidationThrottle()
        self.assertEqual(throttle.rate, '10/hour')


class InvitationValidationSecurityTestCase(APITestCase):
    """Test invitation validation security features (Issue #9)."""

    def setUp(self):
        """Set up test fixtures."""
        from users.models import Invitation
        from master_data.models import Workspace
        from django.utils import timezone
        from datetime import timedelta
        import uuid

        self.client = APIClient()
        cache.clear()

        # Create workspace
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace'
        )

        # Create invitor user
        self.invitor = User.objects.create_user(
            email='invitor@example.com',
            password='testpass123',
            first_name='Invitor',
            last_name='User'
        )

        # Create valid invitation
        self.valid_invitation = Invitation.objects.create(
            email='valid@example.com',
            workspace=self.workspace,
            invitor=self.invitor,
            role='member',
            status='pending',
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Create expired invitation
        self.expired_invitation = Invitation.objects.create(
            email='expired@example.com',
            workspace=self.workspace,
            invitor=self.invitor,
            role='member',
            status='expired',
            expires_at=timezone.now() - timedelta(days=1)
        )

        # Create used invitation
        self.used_invitation = Invitation.objects.create(
            email='used@example.com',
            workspace=self.workspace,
            invitor=self.invitor,
            role='member',
            status='used',
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Create revoked invitation
        self.revoked_invitation = Invitation.objects.create(
            email='revoked@example.com',
            workspace=self.workspace,
            invitor=self.invitor,
            role='member',
            status='revoked',
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Generate non-existent token
        self.nonexistent_token = str(uuid.uuid4())

    def tearDown(self):
        """Clean up after tests."""
        cache.clear()

    def test_valid_invitation_returns_200(self):
        """Test that valid invitation returns 200 OK with details."""
        url = f'/api/v1/invitations/{self.valid_invitation.token}/validate/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['email'], 'valid@example.com')
        self.assertEqual(response.data['workspace_name'], 'Test Workspace')
        self.assertEqual(response.data['message'], 'Invitation is valid')

    def test_nonexistent_token_returns_400_generic_message(self):
        """Test that non-existent token returns 400 with generic message."""
        url = f'/api/v1/invitations/{self.nonexistent_token}/validate/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['message'], 'Invalid or expired invitation')
        # Should NOT contain detailed error like "not found"
        self.assertNotIn('not found', response.data['message'].lower())

    def test_expired_invitation_returns_400_generic_message(self):
        """Test that expired invitation returns 400 with generic message."""
        url = f'/api/v1/invitations/{self.expired_invitation.token}/validate/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['message'], 'Invalid or expired invitation')

    def test_used_invitation_returns_400_generic_message(self):
        """Test that used invitation returns 400 with generic message."""
        url = f'/api/v1/invitations/{self.used_invitation.token}/validate/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['message'], 'Invalid or expired invitation')

    def test_revoked_invitation_returns_400_generic_message(self):
        """Test that revoked invitation returns 400 with generic message."""
        url = f'/api/v1/invitations/{self.revoked_invitation.token}/validate/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['message'], 'Invalid or expired invitation')

    def test_all_failure_cases_return_identical_responses(self):
        """Test that all failure cases return identical status codes and messages."""
        # Get responses for all failure cases
        responses = [
            self.client.get(f'/api/v1/invitations/{self.nonexistent_token}/validate/'),
            self.client.get(f'/api/v1/invitations/{self.expired_invitation.token}/validate/'),
            self.client.get(f'/api/v1/invitations/{self.used_invitation.token}/validate/'),
            self.client.get(f'/api/v1/invitations/{self.revoked_invitation.token}/validate/'),
        ]

        # All should have same status code
        status_codes = [r.status_code for r in responses]
        self.assertEqual(len(set(status_codes)), 1)
        self.assertEqual(status_codes[0], status.HTTP_400_BAD_REQUEST)

        # All should have same message
        messages = [r.data['message'] for r in responses]
        self.assertEqual(len(set(messages)), 1)
        self.assertEqual(messages[0], 'Invalid or expired invitation')

        # All should have valid=False
        valid_flags = [r.data['valid'] for r in responses]
        self.assertTrue(all(v is False for v in valid_flags))

    def test_timing_attack_prevention_similar_response_times(self):
        """Test that response times are similar for different failure cases."""
        import time

        # Test non-existent token timing
        start = time.time()
        self.client.get(f'/api/v1/invitations/{self.nonexistent_token}/validate/')
        nonexistent_time = time.time() - start

        # Test expired token timing
        start = time.time()
        self.client.get(f'/api/v1/invitations/{self.expired_invitation.token}/validate/')
        expired_time = time.time() - start

        # Test used token timing
        start = time.time()
        self.client.get(f'/api/v1/invitations/{self.used_invitation.token}/validate/')
        used_time = time.time() - start

        # Times should be within 100ms of each other (accounting for test overhead)
        # This is a relaxed threshold for testing purposes
        max_diff = max(abs(nonexistent_time - expired_time),
                      abs(nonexistent_time - used_time),
                      abs(expired_time - used_time))

        self.assertLess(max_diff, 0.1,
                       f"Response time variance too high: {max_diff}s")

    def test_rate_limiting_prevents_enumeration(self):
        """Test that rate limiting prevents token enumeration attacks."""
        import uuid

        # Make 11 validation attempts (limit is 10/hour)
        for i in range(11):
            token = str(uuid.uuid4())
            response = self.client.get(f'/api/v1/invitations/{token}/validate/')

            if i < 10:
                # First 10 should return 400 (invalid token)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            else:
                # 11th should be rate limited
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_no_information_disclosure_in_response_fields(self):
        """Test that failure responses don't expose sensitive information."""
        # Non-existent token
        response1 = self.client.get(f'/api/v1/invitations/{self.nonexistent_token}/validate/')

        # Expired token
        response2 = self.client.get(f'/api/v1/invitations/{self.expired_invitation.token}/validate/')

        # Both should only have 'valid' and 'message' fields
        for response in [response1, response2]:
            self.assertIn('valid', response.data)
            self.assertIn('message', response.data)
            self.assertNotIn('status', response.data)
            self.assertNotIn('email', response.data)
            self.assertNotIn('workspace_name', response.data)
            self.assertNotIn('invitor_name', response.data)
            self.assertNotIn('role', response.data)
            self.assertNotIn('expires_at', response.data)

    def test_valid_invitation_exposes_necessary_information(self):
        """Test that valid invitation response contains necessary information."""
        url = f'/api/v1/invitations/{self.valid_invitation.token}/validate/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertIn('email', response.data)
        self.assertIn('workspace_name', response.data)
        self.assertIn('invitor_name', response.data)
        self.assertIn('role', response.data)
        self.assertIn('expires_at', response.data)
