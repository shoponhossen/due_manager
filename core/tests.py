import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from core.exceptions import Error
from core.models import Customer, Product, Due, Deposit


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


class CustomerModelTestCase(TestCase):
    """Test cases for the Customer model."""

    def setUp(self):
        self.user = User.objects.create_user(username="shopkeeper1", password="password123")

    def test_create_customer_with_all_fields(self):
        customer = Customer.objects.create(
            user=self.user,
            name="Alice Smith",
            phone_number="01700000000",
            address="123 Main St, Dhaka"
        )
        self.assertEqual(customer.name, "Alice Smith")
        self.assertEqual(customer.phone_number, "01700000000")
        self.assertEqual(customer.address, "123 Main St, Dhaka")
        self.assertEqual(customer.user, self.user)
        self.assertEqual(str(customer), "Alice Smith")

    def test_customer_optional_fields(self):
        customer = Customer.objects.create(
            user=self.user,
            name="Bob Brown"
        )
        self.assertIsNone(customer.phone_number)
        self.assertIsNone(customer.address)
        self.assertEqual(customer.name, "Bob Brown")

    def test_one_user_can_have_many_customers(self):
        c1 = Customer.objects.create(user=self.user, name="Customer One")
        c2 = Customer.objects.create(user=self.user, name="Customer Two")
        c3 = Customer.objects.create(user=self.user, name="Customer Three")

        self.assertEqual(self.user.customers.count(), 3)
        self.assertIn(c1, self.user.customers.all())
        self.assertIn(c2, self.user.customers.all())
        self.assertIn(c3, self.user.customers.all())

    def test_name_max_length_validation(self):
        long_name = "A" * 31
        customer = Customer(user=self.user, name=long_name)
        with self.assertRaises(ValidationError):
            customer.full_clean()

    def test_total_due_amount_with_no_dues_and_no_deposits(self):
        customer = Customer.objects.create(user=self.user, name="Clean Customer")
        self.assertEqual(customer.total_due_amount(), 0)

    def test_total_due_amount_with_only_dues(self):
        customer = Customer.objects.create(user=self.user, name="Due Customer")
        Due.objects.create(customer=customer, amount=500)
        Due.objects.create(customer=customer, amount=250)

        self.assertEqual(customer.total_due_amount(), 750)

    def test_total_due_amount_with_dues_and_deposits(self):
        customer = Customer.objects.create(user=self.user, name="Active Customer")
        Due.objects.create(customer=customer, amount=1000)
        Due.objects.create(customer=customer, amount=500)
        Deposit.objects.create(customer=customer, amount=300)
        Deposit.objects.create(customer=customer, amount=200)

        # 1500 dues - 500 deposits = 1000
        self.assertEqual(customer.total_due_amount(), 1000)

    def test_total_due_amount_when_fully_paid(self):
        customer = Customer.objects.create(user=self.user, name="Paid Customer")
        Due.objects.create(customer=customer, amount=400)
        Deposit.objects.create(customer=customer, amount=400)

        self.assertEqual(customer.total_due_amount(), 0)

    def test_total_due_amount_with_excess_deposit(self):
        customer = Customer.objects.create(user=self.user, name="Advance Customer")
        Due.objects.create(customer=customer, amount=200)
        Deposit.objects.create(customer=customer, amount=300)

        # Remaining due is -100 (credit/advance)
        self.assertEqual(customer.total_due_amount(), -100)

    def test_total_due_amount_without_deposits_flag(self):
        customer = Customer.objects.create(user=self.user, name="Customer Flag Test")
        Due.objects.create(customer=customer, amount=500)
        Deposit.objects.create(customer=customer, amount=200)

        self.assertEqual(customer.total_due_amount(include_deposits=False), 500)
        self.assertEqual(customer.total_due_amount(include_deposits=True), 300)


class ProductModelTestCase(TestCase):
    """Test cases for the Product model."""

    def test_create_product(self):
        product = Product.objects.create(
            title="Rice",
            quantity=5,
            unit="pice",
            price=250
        )
        self.assertEqual(product.title, "Rice")
        self.assertEqual(product.quantity, 5)
        self.assertEqual(product.unit, "pice")
        self.assertEqual(product.price, 250)
        self.assertIn("Rice", str(product))

    def test_product_units(self):
        p1 = Product.objects.create(title="Sugar", quantity=500, unit="gram", price=60)
        p2 = Product.objects.create(title="Soap", quantity=2, unit="piece", price=80)
        p3 = Product.objects.create(title="Oil", quantity=1, unit="pice", price=120)

        self.assertEqual(p1.unit, "gram")
        self.assertEqual(p2.unit, "piece")
        self.assertEqual(p3.unit, "pice")

    def test_duplicate_products_allowed(self):
        """Verify that duplicate products with same name and same price are allowed."""
        p1 = Product.objects.create(title="Biscuit", quantity=1, unit="pice", price=10)
        p2 = Product.objects.create(title="Biscuit", quantity=1, unit="pice", price=10)

        self.assertNotEqual(p1.id, p2.id)
        self.assertEqual(p1.title, p2.title)
        self.assertEqual(p1.price, p2.price)
        self.assertEqual(Product.objects.filter(title="Biscuit").count(), 2)

    def test_title_max_length_validation(self):
        long_title = "P" * 101
        product = Product(title=long_title, quantity=1, unit="pice", price=10)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_default_values(self):
        product = Product.objects.create(title="Snack")
        self.assertEqual(product.quantity, 1)
        self.assertEqual(product.unit, "pice")
        self.assertEqual(product.price, 0)


class DueModelTestCase(TestCase):
    """Test cases for the Due model."""

    def setUp(self):
        self.user = User.objects.create_user(username="shopkeeper2", password="password123")
        self.customer = Customer.objects.create(user=self.user, name="John Doe")
        self.product1 = Product.objects.create(title="Flour", quantity=2, unit="gram", price=100)
        self.product2 = Product.objects.create(title="Milk", quantity=1, unit="pice", price=80)

    def test_create_due_with_products(self):
        due = Due.objects.create(
            customer=self.customer,
            amount=150  # Discounted from total 180
        )
        due.products.add(self.product1, self.product2)

        self.assertEqual(due.customer, self.customer)
        self.assertEqual(due.amount, 150)
        self.assertFalse(due.is_edited)
        self.assertEqual(due.products.count(), 2)
        self.assertIn(self.product1, due.products.all())
        self.assertIn(self.product2, due.products.all())
        # Singular property alias works as well
        self.assertEqual(due.product.count(), 2)
        self.assertIn(f"Due for {self.customer.name}", str(due))

    def test_one_due_can_have_many_products(self):
        due = Due.objects.create(customer=self.customer, amount=300)
        p1 = Product.objects.create(title="Item 1", price=50)
        p2 = Product.objects.create(title="Item 2", price=75)
        p3 = Product.objects.create(title="Item 3", price=100)

        due.products.add(p1, p2, p3)
        self.assertEqual(due.products.count(), 3)

    def test_one_customer_can_have_many_dues(self):
        due1 = Due.objects.create(customer=self.customer, amount=100)
        due2 = Due.objects.create(customer=self.customer, amount=200)

        self.assertEqual(self.customer.dues.count(), 2)
        self.assertIn(due1, self.customer.dues.all())
        self.assertIn(due2, self.customer.dues.all())

    def test_due_amount_may_differ_from_sum_of_product_prices(self):
        """User can give discount and charge less than total product prices."""
        p1 = Product.objects.create(title="Expensive Item", price=500)
        p2 = Product.objects.create(title="Standard Item", price=200)
        total_products_price = p1.price + p2.price  # 700

        # Shopkeeper gives discount, charges 600
        due = Due.objects.create(customer=self.customer, amount=600)
        due.products.add(p1, p2)

        self.assertNotEqual(due.amount, total_products_price)
        self.assertEqual(due.amount, 600)

    def test_is_edited_flag(self):
        due = Due.objects.create(customer=self.customer, amount=100)
        self.assertFalse(due.is_edited)

        due.amount = 120
        due.is_edited = True
        due.save()

        refreshed_due = Due.objects.get(id=due.id)
        self.assertTrue(refreshed_due.is_edited)
        self.assertEqual(refreshed_due.amount, 120)

    def test_custom_date(self):
        past_date = datetime.date(2026, 1, 15)
        due = Due.objects.create(customer=self.customer, amount=100, date=past_date)
        self.assertEqual(due.date, past_date)


class DepositModelTestCase(TestCase):
    """Test cases for the Deposit model."""

    def setUp(self):
        self.user = User.objects.create_user(username="shopkeeper3", password="password123")
        self.customer = Customer.objects.create(user=self.user, name="Jane Smith")

    def test_create_deposit(self):
        deposit = Deposit.objects.create(
            customer=self.customer,
            amount=500
        )
        self.assertEqual(deposit.customer, self.customer)
        self.assertEqual(deposit.amount, 500)
        self.assertIsNotNone(deposit.date)
        self.assertIn(f"Deposit by {self.customer.name}", str(deposit))

    def test_one_customer_can_have_many_deposits(self):
        d1 = Deposit.objects.create(customer=self.customer, amount=200)
        d2 = Deposit.objects.create(customer=self.customer, amount=300)

        self.assertEqual(self.customer.deposits.count(), 2)
        self.assertIn(d1, self.customer.deposits.all())
        self.assertIn(d2, self.customer.deposits.all())

    def test_custom_deposit_date(self):
        past_date = datetime.date(2026, 5, 20)
        deposit = Deposit.objects.create(customer=self.customer, amount=100, date=past_date)
        self.assertEqual(deposit.date, past_date)


class DueManagerWorkflowTestCase(TestCase):
    """Integration test case for complete shopkeeper due management workflow."""

    def setUp(self):
        self.shopkeeper = User.objects.create_user(username="shopkeeper_workflow", password="password123")
        self.customer = Customer.objects.create(
            user=self.shopkeeper,
            name="Mr. Rahman",
            phone_number="01811111111",
            address="Mirpur, Dhaka"
        )

    def test_complete_due_and_deposit_lifecycle(self):
        # 1. Customer has 0 due initially
        self.assertEqual(self.customer.total_due_amount(), 0)

        # 2. Customer takes goods on Day 1: Due created with multiple products
        tea = Product.objects.create(title="Tea Pack", quantity=1, unit="pice", price=120)
        sugar = Product.objects.create(title="Sugar", quantity=1000, unit="gram", price=130)

        due1 = Due.objects.create(
            customer=self.customer,
            amount=240,  # Shopkeeper discounted 10 tk from 250
            date=datetime.date(2026, 11, 1)
        )
        due1.products.add(tea, sugar)
        self.assertEqual(self.customer.total_due_amount(), 240)

        # 3. Customer takes more goods on Day 2
        oil = Product.objects.create(title="Mustard Oil", quantity=1, unit="pice", price=180)
        due2 = Due.objects.create(
            customer=self.customer,
            amount=180,
            date=datetime.date(2026, 11, 5)
        )
        due2.products.add(oil)
        # Total due is now 240 + 180 = 420
        self.assertEqual(self.customer.total_due_amount(), 420)

        # 4. Customer makes partial deposit on Day 3
        Deposit.objects.create(
            customer=self.customer,
            amount=200,
            date=datetime.date(2026, 11, 7)
        )
        # Total due is now 420 - 200 = 220
        self.assertEqual(self.customer.total_due_amount(), 220)

        # 5. Customer clears remaining due on Day 4
        Deposit.objects.create(
            customer=self.customer,
            amount=220,
            date=datetime.date(2026, 11, 10)
        )
        # Total due is now 0
        self.assertEqual(self.customer.total_due_amount(), 0)

        # 6. Verify cascading delete: deleting customer cleans up their dues and deposits
        cust_id = self.customer.id
        self.customer.delete()
        self.assertEqual(Due.objects.filter(customer_id=cust_id).count(), 0)
        self.assertEqual(Deposit.objects.filter(customer_id=cust_id).count(), 0)
        # Products remain in the catalog
        self.assertTrue(Product.objects.filter(id=tea.id).exists())
