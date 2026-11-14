from django.db import models
from django.utils import timezone
from customer.models import Customer
from product.models import Product


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
