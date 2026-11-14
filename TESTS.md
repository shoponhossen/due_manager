# Test Suite Documentation

## Overview
This document outlines all test cases for the Due Manager API.

---

## Core App Tests (`core/tests.py`)

### CoreExceptionsTestCase
Tests for core exception handling and error responses.

#### API Not Found Tests
- **test_api_not_found_view** - Verify unhandled API routes return 404
- **test_api_not_found_view_post** - Test 404 response for POST requests to non-existent endpoints
- **test_api_not_found_view_nested_route** - Test 404 for deeply nested non-existent routes

#### Custom Error Exception Tests
- **test_custom_error_exception** - Test custom Error exception with default values (400 status)
- **test_custom_error_exception_with_detail** - Test Error exception with custom detail message
- **test_custom_error_exception_with_status_code** - Test Error exception with custom status code
- **test_custom_error_exception_with_both** - Test Error exception with both custom detail and status code

---

## Accounts App Tests (`accounts/tests.py`)

### AccountsAPITestCase
Tests for user authentication and profile management endpoints.

#### User Registration Tests
- **test_user_registration_success** - Successful user registration with valid data
- **test_user_registration_password_mismatch** - Registration fails when password and password_confirm don't match
- **test_user_registration_duplicate_username** - Registration fails with duplicate username
- **test_user_registration_short_password** - Registration fails with password shorter than minimum length
- **test_user_registration_missing_username** - Registration fails when username is not provided

#### Login Tests
- **test_login_success** - Successful login with valid credentials
- **test_login_invalid_username** - Login fails with non-existent username
- **test_login_invalid_password** - Login fails with incorrect password
- **test_login_missing_credentials** - Login fails when credentials are missing

#### Token Management Tests
- **test_token_refresh** - Successfully refresh access token using refresh token
- **test_token_refresh_invalid_token** - Token refresh fails with invalid refresh token

#### Profile Management Tests
- **test_get_profile_authenticated** - Get user profile with valid authentication
- **test_get_profile_unauthenticated** - Getting profile fails without authentication
- **test_update_profile_authenticated** - Update profile fields (first_name, last_name) when authenticated
- **test_update_profile_unauthenticated** - Updating profile fails without authentication
- **test_username_cannot_be_updated** - Username is read-only and cannot be changed after registration

#### Logout Tests
- **test_logout_success** - Successfully logout and blacklist refresh token
- **test_logout_unauthenticated** - Logout fails without authentication
- **test_logout_invalid_token** - Logout fails with invalid refresh token

#### Authentication & Authorization Tests
- **test_authenticated_request_with_valid_token** - Make authenticated request with valid JWT token
- **test_authenticated_request_with_invalid_token** - Request fails with invalid JWT token
- **test_authenticated_request_without_bearer_prefix** - Request fails when Bearer prefix is missing from Authorization header

---

## Test Execution

Run all tests:
```bash
uv run python manage.py test
```

Run specific app tests:
```bash
uv run python manage.py test core
uv run python manage.py test accounts
```

Run specific test case:
```bash
uv run python manage.py test accounts.tests.AccountsAPITestCase.test_login_success
```

---

## Test Coverage Summary

### Core App
- **Total Tests**: 7
- **Coverage**: Exception handling, custom error classes, 404 responses

### Accounts App
- **Total Tests**: 23
- **Coverage**: Registration, login, logout, token management, profile CRUD, authorization

### Overall
- **Total Tests**: 30
- **Authentication**: JWT-based with token blacklisting
- **API**: RESTful endpoints with proper status codes
