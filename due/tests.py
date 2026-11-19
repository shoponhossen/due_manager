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
        self.product1 = Product.objects.create(title="Flour", quantity=2, unit="kg", price=100)
        self.product2 = Product.objects.create(title="Milk", quantity=1, unit="piece", price=80)

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
        tea = Product.objects.create(title="Tea Pack", quantity=1, unit="piece", price=120)
        sugar = Product.objects.create(title="Sugar", quantity=1, unit="kg", price=130)

        due1 = Due.objects.create(
            customer=self.customer,
            amount=240,  # Shopkeeper discounted 10 tk from 250
            date=datetime.date(2026, 11, 1)
        )
        due1.products.add(tea, sugar)
        self.assertEqual(self.customer.total_due_amount(), 240)

        # 3. Customer takes more goods on Day 2
        oil = Product.objects.create(title="Mustard Oil", quantity=1, unit="piece", price=180)
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
                    "title": "Rice",
                    "quantity": 0.500,
                    "unit": "kg",
                    "price": 200,
                },
                {
                    "title": "Lentils",
                    "quantity": 12,
                    "unit": "piece",
                    "price": 30,
                },
            ],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["amount"], 450)
        self.assertEqual(response.data["date"], str(timezone.now().date()))
        self.assertFalse(response.data["is_edited"])
        self.assertEqual(len(response.data["products"]), 2)
        products_by_title = {p["title"]: p for p in response.data["products"]}
        self.assertEqual(products_by_title["Rice"]["quantity"], "0.500")
        self.assertEqual(products_by_title["Rice"]["total_price"], 100)
        self.assertEqual(products_by_title["Lentils"]["total_price"], 360)
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
            "products": [{"title": "Item", "quantity": 1, "unit": "piece", "price": 200}],
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
            "amount": 500,  # Discounted from 900
            "products": [
                {"title": "Oil", "quantity": 2, "unit": "piece", "price": 300},
                {"title": "Spices", "quantity": 1, "unit": "piece", "price": 300},
            ],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["amount"], 500)

    def test_add_due_with_existing_product(self):
        """Due can link to an existing product by id."""
        p = Product.objects.create(title="Existing Biscuit", quantity=1, unit="piece", price=25)
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

    def test_list_dues_requires_customer_id(self):
        """Listing dues requires a customer_id query parameter."""
        response = self.client.get("/api/dues/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_id", response.data)

    def test_list_dues_with_customer_id(self):
        """Listing dues with customer_id returns all dues for that customer."""
        due1 = Due.objects.create(customer=self.customer1, amount=300)
        due2 = Due.objects.create(customer=self.customer1, amount=400)

        response = self.client.get(f"/api/dues/?customer_id={self.customer1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)
        due_ids = [d["id"] for d in results]
        self.assertIn(due1.id, due_ids)
        self.assertIn(due2.id, due_ids)

    def test_list_dues_other_users_customer_returns_404(self):
        """User cannot list dues for another user's customer (returns 404)."""
        Due.objects.create(customer=self.customer2, amount=700)

        # user1 attempts to query user2's customer
        response = self.client.get(f"/api/dues/?customer_id={self.customer2.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_due_cannot_be_edited(self):
        """Dues cannot be edited (PUT/PATCH returns 405 Method Not Allowed)."""
        due = Due.objects.create(customer=self.customer1, amount=100)

        patch_response = self.client.patch(f"/api/dues/{due.id}/", {"amount": 500})
        self.assertEqual(patch_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        put_response = self.client.put(f"/api/dues/{due.id}/", {"amount": 500})
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        due.refresh_from_db()
        self.assertEqual(due.amount, 100)

    def test_due_cannot_be_deleted(self):
        """Dues cannot be deleted (DELETE returns 405 Method Not Allowed)."""
        due = Due.objects.create(customer=self.customer1, amount=100)

        delete_response = self.client.delete(f"/api/dues/{due.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        self.assertTrue(Due.objects.filter(id=due.id).exists())

    def test_due_detail_other_user_forbidden(self):
        """User cannot retrieve detail of another user's due (returns 404)."""
        due_user2 = Due.objects.create(customer=self.customer2, amount=500)

        response = self.client.get(f"/api/dues/{due_user2.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_due_detail_view(self):
        """Detail view returns due with products and customer details."""
        p = Product.objects.create(title="Tea", quantity=1, unit="piece", price=50)
        due = Due.objects.create(customer=self.customer1, amount=50)
        due.products.add(p)

        response = self.client.get(f"/api/dues/{due.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], 50)
        self.assertEqual(response.data["customer"]["id"], self.customer1.id)
        self.assertEqual(len(response.data["products"]), 1)

    def test_add_due_missing_amount_fails(self):
        """Adding due fails with validation error when amount is omitted."""
        payload = {
            "customer_id": self.customer1.id,
            "products": [],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_add_due_case_insensitive_units_and_decimal_qty(self):
        """Units accept Piece/KG case-insensitively and decimal quantities like 0.250."""
        payload = {
            "customer_id": self.customer1.id,
            "amount": 150,
            "products": [
                {"title": "Sugar", "quantity": "0.250", "unit": "KG", "price": 120},
                {"title": "Pen", "quantity": 12, "unit": "Piece", "price": 10},
            ],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        products_by_title = {p["title"]: p for p in response.data["products"]}
        self.assertEqual(products_by_title["Sugar"]["unit"], "kg")
        self.assertEqual(products_by_title["Sugar"]["quantity"], "0.250")
        self.assertEqual(products_by_title["Sugar"]["total_price"], 30)
        self.assertEqual(products_by_title["Pen"]["unit"], "piece")
        self.assertEqual(products_by_title["Pen"]["total_price"], 120)

    def test_add_due_invalid_unit_rejected(self):
        """Removed units like gram or pice are rejected."""
        payload = {
            "customer_id": self.customer1.id,
            "amount": 100,
            "products": [
                {"title": "Sugar", "quantity": 0.5, "unit": "gram", "price": 100},
            ],
        }
        response = self.client.post("/api/dues/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unit", response.data)


class DepositAPITestCase(APITestCase):
    """Test cases for Deposit REST API endpoints (Create, List, Detail)."""

    def setUp(self):
        self.user1 = User.objects.create_user(username="shopkeeper_dep1", password="password123")
        self.user2 = User.objects.create_user(username="shopkeeper_dep2", password="password123")

        self.customer1 = Customer.objects.create(user=self.user1, name="Customer Dep One")
        self.customer2 = Customer.objects.create(user=self.user2, name="Customer Dep Two")

        refresh1 = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh1.access_token)

        refresh2 = RefreshToken.for_user(self.user2)
        self.token2 = str(refresh2.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")

    def test_create_deposit_success(self):
        """User creates deposit for their customer; total_due_amount decreases."""
        Due.objects.create(customer=self.customer1, amount=1000)
        self.assertEqual(self.customer1.total_due_amount(), 1000)

        payload = {
            "customer_id": self.customer1.id,
            "amount": 400,
        }
        response = self.client.post("/api/deposits/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["amount"], 400)
        self.assertEqual(response.data["date"], str(timezone.now().date()))
        self.assertEqual(response.data["customer"]["id"], self.customer1.id)

        # Total due amount is now 1000 - 400 = 600
        self.assertEqual(self.customer1.total_due_amount(), 600)

    def test_create_deposit_missing_amount(self):
        """Creating deposit fails when amount is omitted."""
        payload = {"customer_id": self.customer1.id}
        response = self.client.post("/api/deposits/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)

    def test_create_deposit_missing_customer_id(self):
        """Creating deposit fails when customer_id is omitted."""
        payload = {"amount": 500}
        response = self.client.post("/api/deposits/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_id", response.data)

    def test_create_deposit_other_users_customer_forbidden(self):
        """User cannot create a deposit for another shopkeeper's customer."""
        payload = {
            "customer_id": self.customer2.id,
            "amount": 300,
        }
        response = self.client.post("/api/deposits/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("customer_id", response.data)

    def test_create_deposit_date_cannot_be_changed_via_user(self):
        """User-supplied date is ignored; defaults to today."""
        payload = {
            "customer_id": self.customer1.id,
            "amount": 250,
            "date": "2020-01-01",
        }
        response = self.client.post("/api/deposits/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["date"], str(timezone.now().date()))

    def test_create_deposit_unauthenticated(self):
        """Unauthenticated request to create deposit fails."""
        self.client.credentials()
        payload = {
            "customer_id": self.customer1.id,
            "amount": 200,
        }
        response = self.client.post("/api/deposits/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_deposits_all_user_customers(self):
        """Listing deposits returns deposits of shopkeeper's customers."""
        d1 = Deposit.objects.create(customer=self.customer1, amount=100)
        d2 = Deposit.objects.create(customer=self.customer1, amount=200)
        # Another user's deposit
        Deposit.objects.create(customer=self.customer2, amount=500)

        response = self.client.get("/api/deposits/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)
        deposit_ids = [d["id"] for d in results]
        self.assertIn(d1.id, deposit_ids)
        self.assertIn(d2.id, deposit_ids)

    def test_list_deposits_filtered_by_customer_id(self):
        """Listing deposits can be filtered by customer_id."""
        c1b = Customer.objects.create(user=self.user1, name="Customer Dep 1B")
        d1 = Deposit.objects.create(customer=self.customer1, amount=150)
        Deposit.objects.create(customer=c1b, amount=350)

        response = self.client.get(f"/api/deposits/?customer_id={self.customer1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], d1.id)

    def test_list_deposits_other_user_customer_returns_404(self):
        """Filtering deposits by another user's customer returns 404."""
        response = self.client.get(f"/api/deposits/?customer_id={self.customer2.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deposit_detail_view(self):
        """Detail view returns full deposit information."""
        deposit = Deposit.objects.create(customer=self.customer1, amount=750)

        response = self.client.get(f"/api/deposits/{deposit.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], 750)
        self.assertEqual(response.data["customer"]["id"], self.customer1.id)

    def test_deposit_detail_other_user_forbidden(self):
        """User cannot access detail of another user's deposit (returns 404)."""
        dep_user2 = Deposit.objects.create(customer=self.customer2, amount=800)

        response = self.client.get(f"/api/deposits/{dep_user2.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deposit_cannot_be_edited(self):
        """Deposits cannot be edited (PUT/PATCH returns 405 Method Not Allowed)."""
        deposit = Deposit.objects.create(customer=self.customer1, amount=300)

        patch_res = self.client.patch(f"/api/deposits/{deposit.id}/", {"amount": 900})
        self.assertEqual(patch_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        put_res = self.client.put(f"/api/deposits/{deposit.id}/", {"amount": 900})
        self.assertEqual(put_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        deposit.refresh_from_db()
        self.assertEqual(deposit.amount, 300)

    def test_deposit_cannot_be_deleted(self):
        """Deposits cannot be deleted (DELETE returns 405 Method Not Allowed)."""
        deposit = Deposit.objects.create(customer=self.customer1, amount=300)

        del_res = self.client.delete(f"/api/deposits/{deposit.id}/")
        self.assertEqual(del_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Deposit.objects.filter(id=deposit.id).exists())
