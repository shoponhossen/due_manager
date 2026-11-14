from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AccountsAPITestCase(APITestCase):
    """Test cases for accounts API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('profile')
        self.token_refresh_url = reverse('token_refresh')

        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.valid_registration_data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }

        self.valid_login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

    def test_user_registration_success(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.valid_registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_registration_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        data = self.valid_registration_data.copy()
        data['password_confirm'] = 'differentpass'

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_duplicate_username(self):
        """Test registration fails with duplicate username."""
        data = self.valid_registration_data.copy()
        data['username'] = 'testuser'  # Already exists

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_short_password(self):
        """Test registration fails with short password."""
        data = self.valid_registration_data.copy()
        data['password'] = '12345'
        data['password_confirm'] = '12345'

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_missing_username(self):
        """Test registration fails without username."""
        data = self.valid_registration_data.copy()
        data.pop('username')

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post(self.login_url, self.valid_login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_login_invalid_username(self):
        """Test login fails with invalid username."""
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }

        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_invalid_password(self):
        """Test login fails with invalid password."""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }

        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_missing_credentials(self):
        """Test login fails with missing credentials."""
        response = self.client.post(self.login_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh(self):
        """Test token refresh."""
        # Login to get tokens
        login_response = self.client.post(self.login_url, self.valid_login_data)
        refresh_token = login_response.data['refresh']

        # Refresh the token
        response = self.client.post(self.token_refresh_url, {'refresh': refresh_token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid_token(self):
        """Test token refresh fails with invalid token."""
        response = self.client.post(self.token_refresh_url, {'refresh': 'invalid_token'})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_authenticated(self):
        """Test getting profile when authenticated."""
        # Login to get access token
        login_response = self.client.post(self.login_url, self.valid_login_data)
        access_token = login_response.data['access']

        # Get profile with authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_get_profile_unauthenticated(self):
        """Test getting profile fails when not authenticated."""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_authenticated(self):
        """Test updating profile when authenticated."""
        # Login to get access token
        login_response = self.client.post(self.login_url, self.valid_login_data)
        access_token = login_response.data['access']

        # Update profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')

        # Verify in database
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.first_name, 'Updated')
        self.assertEqual(self.test_user.last_name, 'Name')

    def test_update_profile_unauthenticated(self):
        """Test updating profile fails when not authenticated."""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        """Test successful logout."""
        # Login to get tokens
        login_response = self.client.post(self.login_url, self.valid_login_data)
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']

        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.logout_url, {'refresh': refresh_token})

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertIn('message', response.data)

    def test_logout_unauthenticated(self):
        """Test logout fails when not authenticated."""
        response = self.client.post(self.logout_url, {'refresh': 'some_token'})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_token(self):
        """Test logout fails with invalid refresh token."""
        # Login to get access token
        login_response = self.client.post(self.login_url, self.valid_login_data)
        access_token = login_response.data['access']

        # Try to logout with invalid refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.logout_url, {'refresh': 'invalid_token'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_authenticated_request_with_valid_token(self):
        """Test making authenticated request with valid token."""
        # Login to get access token
        login_response = self.client.post(self.login_url, self.valid_login_data)
        access_token = login_response.data['access']

        # Make authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_request_with_invalid_token(self):
        """Test making authenticated request with invalid token."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_request_without_bearer_prefix(self):
        """Test making authenticated request without Bearer prefix."""
        # Login to get access token
        login_response = self.client.post(self.login_url, self.valid_login_data)
        access_token = login_response.data['access']

        # Try without Bearer prefix
        self.client.credentials(HTTP_AUTHORIZATION=access_token)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_username_cannot_be_updated(self):
        """Test that username is read-only and cannot be updated after registration."""
        login_response = self.client.post(self.login_url, self.valid_login_data)
        access_token = login_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.patch(self.profile_url, {
            'username': 'newusername',
            'first_name': 'Updated',
            'last_name': 'Name'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Username stays unchanged
        self.assertEqual(response.data['username'], 'testuser')
        # Other fields updated
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        # Verify in DB
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.username, 'testuser')
