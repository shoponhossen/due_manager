from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Customer(models.Model):
    """
    Customer model representing a customer of the shopkeeper.
    One User (shopkeeper) can have many Customers.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customers"
    )
    name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name

    def total_due_amount(self, include_deposits=True):
        """
        Calculates the customer's total due amount.
        By default, total dues minus total deposits.
        """
        total_dues = self.dues.aggregate(total=models.Sum("amount"))["total"] or 0
        if not include_deposits:
            return total_dues
        total_deposits = self.deposits.aggregate(total=models.Sum("amount"))["total"] or 0
        return total_dues - total_deposits


class Product(models.Model):
    """
    Product model representing items associated with dues.
    Duplicates with the same name and price are allowed.
    """
    class UnitChoices(models.TextChoices):
        GRAM = "gram", "Gram"
        PICE = "pice", "Pice"
        PIECE = "piece", "Piece"

    title = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(
        max_length=10,
        choices=UnitChoices.choices,
        default=UnitChoices.PICE
    )
    price = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.title} ({self.quantity} {self.unit})"

    @property
    def due(self):
        """Returns the first associated due if accessed from the product side."""
        return self.dues.first()


class Due(models.Model):
    """
    Due model representing an unpaid balance record for a customer.
    One Customer can have many Dues.
    One Due can have many Products.
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="dues"
    )
    products = models.ManyToManyField(
        Product,
        related_name="dues",
        blank=True
    )
    date = models.DateField(default=timezone.now)
    is_edited = models.BooleanField(default=False)
    amount = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Due for {self.customer.name} - {self.amount}"

    @property
    def product(self):
        """Alias for products to support both singular and plural attribute access."""
        return self.products


class Deposit(models.Model):
    """
    Deposit model representing a payment made by a customer against their dues.
    One Customer can have many Deposits.
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="deposits"
    )
    amount = models.PositiveIntegerField(default=0)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Deposit by {self.customer.name} - {self.amount}"
