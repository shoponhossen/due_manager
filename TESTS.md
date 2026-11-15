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

## Customer App Tests (`customer/tests.py`)

### CustomerModelTestCase
Tests for Customer model attributes, validation, relationships, and balance calculations.
- **test_create_customer_with_all_fields** - Test creating customer with user, name, phone_number, and address
- **test_customer_optional_fields** - Test creating customer with optional fields omitted
- **test_one_user_can_have_many_customers** - Verify 1-to-many relationship between User and Customer
- **test_name_max_length_validation** - Verify name field enforces max length of 30 characters
- **test_total_due_amount_with_no_dues_and_no_deposits** - Initial balance is 0
- **test_total_due_amount_with_only_dues** - Balance reflects sum of all dues
- **test_total_due_amount_with_dues_and_deposits** - Balance reflects dues minus deposits
- **test_total_due_amount_when_fully_paid** - Balance returns 0 when dues equals deposits
- **test_total_due_amount_with_excess_deposit** - Balance returns negative when deposits exceed dues
- **test_total_due_amount_without_deposits_flag** - Optional flag to compute gross due amount without subtracting deposits

### CustomerAPITestCase
Tests for Customer REST endpoints.
- **test_create_customer_success** - Shopkeeper creates customer with all details; total_due_amount starts at 0
- **test_create_customer_minimal_fields** - Create customer with only required name field
- **test_create_customer_missing_name** - Validation error when name is missing
- **test_create_customer_name_too_long** - Validation error when name exceeds 30 characters
- **test_create_customer_unauthenticated** - Returns 401 when unauthenticated
- **test_list_customers_fields** - List returns name, phone_number, and calculated total_due_amount
- **test_list_customers_multi_tenancy_isolation** - Shopkeeper only sees their own customers
- **test_customer_detail_view** - Detail view returns address, phone_number, and total_due_amount
- **test_customer_detail_other_user_forbidden** - Accessing another shopkeeper's customer returns 404
- **test_customer_cannot_be_edited** - Customers cannot be edited (PATCH/PUT returns 405 Method Not Allowed)
- **test_customer_cannot_be_deleted** - Customers cannot be deleted (DELETE returns 405 Method Not Allowed)

---

## Product App Tests (`product/tests.py`)

### ProductModelTestCase
Tests for Product model attributes, units, prices, and deduplication rules.
- **test_create_product** - Test creating product with title, quantity, unit, and price
- **test_product_units** - Test supported unit choices (gram, pice, piece)
- **test_duplicate_products_allowed** - Verify multiple products can share the same name and price
- **test_title_max_length_validation** - Verify title field enforces max length of 100 characters
- **test_default_values** - Verify default quantity, unit, and price values

---

## Due App Tests (`due/tests.py`)

### DueModelTestCase
Tests for Due model creation, relationships, and discount amount overrides.
- **test_create_due_with_products** - Test creating due with multiple products and custom amount
- **test_one_due_can_have_many_products** - Verify 1-to-many / M2M relationship between Due and Products
- **test_one_customer_can_have_many_dues** - Verify 1-to-many relationship between Customer and Dues
- **test_due_amount_may_differ_from_sum_of_product_prices** - Verify shopkeeper discount / custom amount
- **test_is_edited_flag** - Verify is_edited boolean flag defaulting to False and updateable to True
- **test_custom_date** - Test recording due with a specific historical date

### DepositModelTestCase
Tests for Deposit model creation, amounts, and dates.
- **test_create_deposit** - Test creating deposit with customer, amount, and date
- **test_one_customer_can_have_many_deposits** - Verify 1-to-many relationship between Customer and Deposits
- **test_custom_deposit_date** - Test recording deposit with a specific historical date

### DueManagerWorkflowTestCase
- **test_complete_due_and_deposit_lifecycle** - End-to-end integration test verifying day-by-day due tracking, deposits, running balance, and cascade deletion

### DueAPITestCase
Tests for Due REST API endpoints.
- **test_add_due_all_at_once_success** - Add due providing customer_id, products, and amount in a single request; total_due_amount updates
- **test_add_due_date_cannot_be_changed_via_user** - User-supplied date is ignored; due date defaults to today
- **test_add_due_is_edited_cannot_be_changed_via_user** - User-supplied is_edited is ignored; defaults to False
- **test_add_due_discounted_amount** - Due amount can differ from sum of product prices
- **test_add_due_with_existing_product** - Due can reference existing product by id
- **test_add_due_invalid_customer** - Fails when customer_id does not exist
- **test_add_due_other_users_customer_forbidden** - Fails when customer belongs to another shopkeeper
- **test_add_due_unauthenticated** - Returns 401 when unauthenticated
- **test_list_dues_requires_customer_id** - Listing dues requires a customer_id query parameter
- **test_list_dues_with_customer_id** - Listing dues with customer_id returns all dues for that customer
- **test_list_dues_other_users_customer_returns_404** - User cannot query another user's customer dues (returns 404)
- **test_due_cannot_be_edited** - Dues cannot be edited (PUT/PATCH returns 405 Method Not Allowed)
- **test_due_cannot_be_deleted** - Dues cannot be deleted (DELETE returns 405 Method Not Allowed)
- **test_due_detail_other_user_forbidden** - User cannot retrieve detail of another user's due (returns 404)
- **test_due_detail_view** - Detail view returns full product and customer data

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
- **Total Tests**: 32
- **Coverage**: Exception handling, custom error classes, 404 responses, Customer, Product, Due, Deposit models, validation, and due/deposit lifecycle calculations

### Accounts App
- **Total Tests**: 22
- **Coverage**: Registration, login, logout, token management, profile CRUD, authorization

### Overall
- **Total Tests**: 54
- **Authentication**: JWT-based with token blacklisting
- **API**: RESTful endpoints with proper status codes
- **Models**: Business logic, relationships, calculations, and constraints
