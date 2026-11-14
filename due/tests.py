import datetime
from django.test import TestCase
from django.contrib.auth.models import User

from customer.models import Customer
from product.models import Product
from due.models import Due, Deposit


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
