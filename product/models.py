from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """
    Product model representing items associated with dues.
    Duplicates with the same name and price are allowed.
    """
    class UnitChoices(models.TextChoices):
        PIECE = "piece", "Piece"
        KG = "kg", "KG"

    title = models.CharField(max_length=100)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal("1.000"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    unit = models.CharField(
        max_length=10,
        choices=UnitChoices.choices,
        default=UnitChoices.PIECE,
    )
    price = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    @property
    def total_price(self):
        """Calculates total price as quantity * unit price."""
        total = Decimal(str(self.quantity)) * Decimal(self.price)
        if total == total.to_integral_value():
            return int(total)
        return float(total)

    def __str__(self):
        qty = Decimal(str(self.quantity))
        if qty == qty.to_integral_value():
            qty_display = str(int(qty))
        else:
            qty_display = f"{qty.quantize(Decimal('0.001'))}"
        return f"{qty_display} {self.get_unit_display()} {self.title} price is {self.total_price}"

    @property
    def due(self):
        """Returns the first associated due if accessed from the product side."""
        return self.dues.first()
