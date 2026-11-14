from django.test import TestCase
from django.core.exceptions import ValidationError

from product.models import Product


class ProductModelTestCase(TestCase):
    """Test cases for the Product model."""

    def test_create_product(self):
        product = Product.objects.create(
            title="Rice",
            quantity=5,
            unit="pice",
            price=250
        )
        self.assertEqual(product.title, "Rice")
        self.assertEqual(product.quantity, 5)
        self.assertEqual(product.unit, "pice")
        self.assertEqual(product.price, 250)
        self.assertIn("Rice", str(product))

    def test_product_units(self):
        p1 = Product.objects.create(title="Sugar", quantity=500, unit="gram", price=60)
        p2 = Product.objects.create(title="Soap", quantity=2, unit="piece", price=80)
        p3 = Product.objects.create(title="Oil", quantity=1, unit="pice", price=120)

        self.assertEqual(p1.unit, "gram")
        self.assertEqual(p2.unit, "piece")
        self.assertEqual(p3.unit, "pice")

    def test_duplicate_products_allowed(self):
        """Verify that duplicate products with same name and same price are allowed."""
        p1 = Product.objects.create(title="Biscuit", quantity=1, unit="pice", price=10)
        p2 = Product.objects.create(title="Biscuit", quantity=1, unit="pice", price=10)

        self.assertNotEqual(p1.id, p2.id)
        self.assertEqual(p1.title, p2.title)
        self.assertEqual(p1.price, p2.price)
        self.assertEqual(Product.objects.filter(title="Biscuit").count(), 2)

    def test_title_max_length_validation(self):
        long_title = "P" * 101
        product = Product(title=long_title, quantity=1, unit="pice", price=10)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_default_values(self):
        product = Product.objects.create(title="Snack")
        self.assertEqual(product.quantity, 1)
        self.assertEqual(product.unit, "pice")
        self.assertEqual(product.price, 0)
