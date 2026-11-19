from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

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


class CustomerAPITestCase(APITestCase):
    """Test cases for Customer REST API endpoints."""

    def setUp(self):
        self.user1 = User.objects.create_user(username="shopkeeper_api1", password="password123")
        self.user2 = User.objects.create_user(username="shopkeeper_api2", password="password123")

        refresh1 = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh1.access_token)

        refresh2 = RefreshToken.for_user(self.user2)
        self.token2 = str(refresh2.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")

    def test_create_customer_success(self):
        """User can create a new customer with all details."""
        payload = {
            "name": "Mahmud Hasan",
            "phone_number": "01711223344",
            "address": "Dhanmondi, Dhaka",
        }
        response = self.client.post("/api/customers/", payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Mahmud Hasan")
        self.assertEqual(response.data["phone_number"], "01711223344")
        self.assertEqual(response.data["address"], "Dhanmondi, Dhaka")
        self.assertEqual(response.data["total_due_amount"], 0)

        # Confirm customer created in DB under user1
        customer = Customer.objects.get(id=response.data["id"])
        self.assertEqual(customer.user, self.user1)

    def test_create_customer_minimal_fields(self):
        """User can create customer with only required fields (name)."""
        payload = {"name": "Only Name"}
        response = self.client.post("/api/customers/", payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Only Name")
        self.assertIsNone(response.data["phone_number"])
        self.assertIsNone(response.data["address"])

    def test_create_customer_missing_name(self):
        """Customer creation fails without a name."""
        payload = {"phone_number": "01711223344"}
        response = self.client.post("/api/customers/", payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_customer_name_too_long(self):
        """Customer creation fails if name exceeds 30 characters."""
        payload = {"name": "A" * 31}
        response = self.client.post("/api/customers/", payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_customer_unauthenticated(self):
        """Unauthenticated user cannot create a customer."""
        self.client.credentials()  # Remove auth
        response = self.client.post("/api/customers/", {"name": "Unauth Cust"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_customers_fields(self):
        """List view returns name, phone_number, address, and total_due_amount."""
        c1 = Customer.objects.create(
            user=self.user1,
            name="Customer A",
            phone_number="01911111111",
            address="Mirpur, Dhaka",
        )
        Due.objects.create(customer=c1, amount=600)
        Deposit.objects.create(customer=c1, amount=150)

        response = self.client.get("/api/customers/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["name"], "Customer A")
        self.assertEqual(item["phone_number"], "01911111111")
        self.assertEqual(item["address"], "Mirpur, Dhaka")
        self.assertEqual(item["total_due_amount"], 450)  # 600 - 150

    def test_list_customers_multi_tenancy_isolation(self):
        """User only sees their own customers, not customers of other users."""
        Customer.objects.create(user=self.user1, name="User1 Customer")
        Customer.objects.create(user=self.user2, name="User2 Customer")

        response = self.client.get("/api/customers/")
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "User1 Customer")

        # Now test with user2 credentials
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token2}")
        response2 = self.client.get("/api/customers/")
        results2 = response2.data.get("results", response2.data)
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["name"], "User2 Customer")

    def test_customer_detail_view(self):
        """Detail view returns full customer details including address and total_due_amount."""
        c = Customer.objects.create(
            user=self.user1,
            name="Detailed Cust",
            phone_number="01800000000",
            address="Gulshan, Dhaka"
        )
        Due.objects.create(customer=c, amount=1200)

        response = self.client.get(f"/api/customers/{c.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detailed Cust")
        self.assertEqual(response.data["phone_number"], "01800000000")
        self.assertEqual(response.data["address"], "Gulshan, Dhaka")
        self.assertEqual(response.data["total_due_amount"], 1200)

    def test_customer_detail_other_user_forbidden(self):
        """User cannot view detail of another user's customer (returns 404)."""
        other_customer = Customer.objects.create(user=self.user2, name="Secret Cust")
        response = self.client.get(f"/api/customers/{other_customer.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_cannot_be_edited(self):
        """Customers cannot be edited (PATCH/PUT returns 405 Method Not Allowed)."""
        c = Customer.objects.create(user=self.user1, name="Original Name")
        patch_response = self.client.patch(f"/api/customers/{c.id}/", {"name": "Changed"})
        self.assertEqual(patch_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        put_response = self.client.put(f"/api/customers/{c.id}/", {"name": "Changed"})
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Name in DB is unchanged
        c.refresh_from_db()
        self.assertEqual(c.name, "Original Name")

    def test_customer_cannot_be_deleted(self):
        """Customers cannot be deleted (DELETE returns 405 Method Not Allowed)."""
        c = Customer.objects.create(user=self.user1, name="Protected Customer")
        response = self.client.delete(f"/api/customers/{c.id}/")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Customer.objects.filter(id=c.id).exists())
