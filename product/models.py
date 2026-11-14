from django.db import models


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
