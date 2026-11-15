import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

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


class DueAPITestCase(APITestCase):
    """Test cases for Due REST API endpoints (Add Due, List, Detail)."""

    def setUp(self):
        self.user1 = User.objects.create_user(username="shopkeeper_due1", password="password123")
        self.user2 = User.objects.create_user(username="shopkeeper_due2", password="password123")

        self.customer1 = Customer.objects.create(user=self.user1, name="Customer One")
        self.customer2 = Customer.objects.create(user=self.user2, name="Customer Two")

        refresh1 = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh1.access_token)

        refresh2 = RefreshToken.for_user(self.user2)
        self.token2 = str(refresh2.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")

    def test_add_due_all_at_once_success(self):
        """User provides all data at once: customer_id, products, and amount."""
        payload = {
            "customer_id": self.customer1.id,
            "amount": 450,
            "products": [
                {
                    "title": "Rice 5kg",
                    "quantity": 1,
                    "unit": "pice",
                    "price": 320,
                },
                {
                    "title": "Lentils",
                    "quantity": 1000,
                    "unit": "gram",
                    "price": 140,
                },
            ],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["amount"], 450)
        self.assertEqual(response.data["date"], str(timezone.now().date()))
        self.assertFalse(response.data["is_edited"])
        self.assertEqual(len(response.data["products"]), 2)
        self.assertEqual(response.data["customer"]["id"], self.customer1.id)

        # Verify DB records
        due = Due.objects.get(id=response.data["id"])
        self.assertEqual(due.products.count(), 2)
        self.assertEqual(due.amount, 450)

        # Verify customer's total due amount is updated
        self.assertEqual(self.customer1.total_due_amount(), 450)

    def test_add_due_date_cannot_be_changed_via_user(self):
        """User cannot override the date when adding a due."""
        payload = {
            "customer_id": self.customer1.id,
            "amount": 200,
            "date": "2020-01-01",  # User tries to pass past date
            "products": [{"title": "Item", "quantity": 1, "unit": "pice", "price": 200}],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Date must still be today, ignoring user input
        self.assertEqual(response.data["date"], str(timezone.now().date()))
        due = Due.objects.get(id=response.data["id"])
        self.assertEqual(due.date, timezone.now().date())

    def test_add_due_is_edited_cannot_be_changed_via_user(self):
        """User cannot override the is_edited flag when adding a due."""
        payload = {
            "customer_id": self.customer1.id,
            "amount": 100,
            "is_edited": True,  # User tries to pass is_edited True
            "products": [],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_edited"])
        due = Due.objects.get(id=response.data["id"])
        self.assertFalse(due.is_edited)

    def test_add_due_discounted_amount(self):
        """Amount may differ from sum of product prices (shopkeeper discount)."""
        payload = {
            "customer_id": self.customer1.id,
            "amount": 500,  # Discounted from 600
            "products": [
                {"title": "Oil", "quantity": 2, "unit": "pice", "price": 300},
                {"title": "Spices", "quantity": 1, "unit": "pice", "price": 300},
            ],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["amount"], 500)

    def test_add_due_with_existing_product(self):
        """Due can link to an existing product by id."""
        p = Product.objects.create(title="Existing Biscuit", quantity=1, unit="pice", price=25)
        payload = {
            "customer_id": self.customer1.id,
            "amount": 25,
            "products": [{"id": p.id}],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["products"]), 1)
        self.assertEqual(response.data["products"][0]["id"], p.id)

    def test_add_due_invalid_customer(self):
        """Adding due fails with invalid customer_id."""
        payload = {
            "customer_id": 99999,
            "amount": 100,
            "products": [],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_id", response.data)

    def test_add_due_other_users_customer_forbidden(self):
        """User cannot add a due to another user's customer."""
        payload = {
            "customer_id": self.customer2.id,  # customer2 belongs to user2
            "amount": 100,
            "products": [],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_id", response.data)

    def test_add_due_unauthenticated(self):
        """Unauthenticated request to add due fails."""
        self.client.credentials()  # Remove auth
        payload = {
            "customer_id": self.customer1.id,
            "amount": 100,
            "products": [],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_dues_multi_tenancy(self):
        """User only retrieves dues associated with their own customers."""
        due1 = Due.objects.create(customer=self.customer1, amount=300)
        Due.objects.create(customer=self.customer2, amount=700)

        response = self.client.get("/api/dues/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], due1.id)

    def test_due_detail_view(self):
        """Detail view returns due with products and customer details."""
        p = Product.objects.create(title="Tea", quantity=1, unit="pice", price=50)
        due = Due.objects.create(customer=self.customer1, amount=50)
        due.products.add(p)

        response = self.client.get(f"/api/dues/{due.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], 50)
        self.assertEqual(response.data["customer"]["id"], self.customer1.id)
        self.assertEqual(len(response.data["products"]), 1)
