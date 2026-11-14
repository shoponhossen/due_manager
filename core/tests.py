from rest_framework.test import APITestCase
from rest_framework import status
from core.exceptions import Error


class CoreExceptionsTestCase(APITestCase):
    """Test cases for core exception handling."""

    def test_api_not_found_view(self):
        """Test that unhandled API routes return DRF 404."""
        response = self.client.get('/api/nonexistent/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'The resource you are looking for is not found.')

    def test_api_not_found_view_post(self):
        """Test 404 view with POST method."""
        response = self.client.post('/api/nonexistent/', {})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

    def test_api_not_found_view_nested_route(self):
        """Test 404 view with deeply nested route."""
        response = self.client.get('/api/some/nested/route/that/does/not/exist/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

    def test_custom_error_exception(self):
        """Test custom Error exception with default values."""
        error = Error()

        self.assertEqual(error.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(error.detail, "A custom business error occurred.")
        self.assertEqual(error.default_code, "custom_error")

    def test_custom_error_exception_with_detail(self):
        """Test custom Error exception with custom detail."""
        custom_detail = "Something went wrong with your request."
        error = Error(detail=custom_detail)

        self.assertEqual(error.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(error.detail, custom_detail)

    def test_custom_error_exception_with_status_code(self):
        """Test custom Error exception with custom status code."""
        error = Error(status_code=status.HTTP_403_FORBIDDEN)

        self.assertEqual(error.status_code, status.HTTP_403_FORBIDDEN)

    def test_custom_error_exception_with_both(self):
        """Test custom Error exception with both detail and status code."""
        custom_detail = "Unauthorized access."
        error = Error(detail=custom_detail, status_code=status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(error.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(error.detail, custom_detail)
