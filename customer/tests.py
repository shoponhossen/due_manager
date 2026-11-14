from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from customer.models import Customer
from due.models import Due, Deposit


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
