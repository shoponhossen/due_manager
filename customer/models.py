from django.db import models
from django.contrib.auth.models import User


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
