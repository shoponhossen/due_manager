from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from product.models import Product


class ProductModelTestCase(TestCase):
    """Test cases for the Product model."""

    def test_create_product(self):
        product = Product.objects.create(
            title="Rice",
            quantity=Decimal("0.500"),
            unit="kg",
            price=200,
        )
        self.assertEqual(product.title, "Rice")
        self.assertEqual(product.quantity, Decimal("0.500"))
        self.assertEqual(product.unit, "kg")
        self.assertEqual(product.price, 200)
        self.assertEqual(product.total_price, 100)
        self.assertEqual(str(product), "0.500 KG Rice price is 100")

    def test_product_units(self):
        p1 = Product.objects.create(title="Sugar", quantity=Decimal("0.250"), unit="kg", price=120)
        p2 = Product.objects.create(title="Soap", quantity=12, unit="piece", price=30)

        self.assertEqual(p1.unit, "kg")
        self.assertEqual(p1.total_price, 30)
        self.assertEqual(str(p1), "0.250 KG Sugar price is 30")

        self.assertEqual(p2.unit, "piece")
        self.assertEqual(p2.total_price, 360)
        self.assertEqual(str(p2), "12 Piece Soap price is 360")

    def test_invalid_legacy_units_rejected(self):
        """Only piece and kg units are allowed; gram and pice are rejected."""
        for invalid_unit in ("gram", "pice", "liter"):
            product = Product(title="Item", quantity=1, unit=invalid_unit, price=10)
            with self.assertRaises(ValidationError):
                product.full_clean()

    def test_decimal_quantity_and_fractional_total_price(self):
        product = Product.objects.create(
            title="Lentils",
            quantity=Decimal("0.250"),
            unit="kg",
            price=50,
        )
        self.assertEqual(product.total_price, 12.5)

    def test_negative_quantity_rejected(self):
        product = Product(title="Rice", quantity=Decimal("-0.500"), unit="kg", price=100)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_duplicate_products_allowed(self):
        """Verify that duplicate products with same name and same price are allowed."""
        p1 = Product.objects.create(title="Biscuit", quantity=1, unit="piece", price=10)
        p2 = Product.objects.create(title="Biscuit", quantity=1, unit="piece", price=10)

        self.assertNotEqual(p1.id, p2.id)
        self.assertEqual(p1.title, p2.title)
        self.assertEqual(p1.price, p2.price)
        self.assertEqual(Product.objects.filter(title="Biscuit").count(), 2)

    def test_title_max_length_validation(self):
        long_title = "P" * 101
        product = Product(title=long_title, quantity=1, unit="piece", price=10)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_default_values(self):
        product = Product.objects.create(title="Snack")
        self.assertEqual(product.quantity, Decimal("1.000"))
        self.assertEqual(product.unit, "piece")
        self.assertEqual(product.price, 0)
        self.assertEqual(product.total_price, 0)
