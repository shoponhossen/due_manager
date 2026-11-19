from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from .models import Due, Deposit
from customer.models import Customer
from customer.serializers import CustomerListSerializer
from product.models import Product
from product.serializers import ProductSerializer


class DueSerializer(serializers.ModelSerializer):
    """
    Serializer for Due records.
    Handles adding due with customer_id, products, and amount all at once.
    date and is_edited cannot be changed by the user.
    """
    customer_id = serializers.IntegerField(write_only=True, required=False)
    customer = CustomerListSerializer(read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    date = serializers.DateField(read_only=True)
    is_edited = serializers.BooleanField(read_only=True)

    class Meta:
        model = Due
        fields = [
            "id",
            "customer",
            "customer_id",
            "amount",
            "products",
            "date",
            "is_edited",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "products",
            "date",
            "is_edited",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "amount": {"required": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Handle customer_id resolution and ownership
        customer_id = attrs.get("customer_id")
        # In case client passes 'customer' as an integer in initial_data
        if not customer_id and self.initial_data.get("customer"):
            try:
                customer_id = int(self.initial_data["customer"])
            except (ValueError, TypeError):
                pass

        if not customer_id:
            raise serializers.ValidationError({
                "customer_id": ["This field is required."]
            })

        try:
            customer = Customer.objects.get(id=customer_id, user=user)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({
                "customer_id": ["Customer not found or does not belong to you."]
            })

        attrs["customer_instance"] = customer

        # Extract products input from initial_data
        products_raw = self.initial_data.get("products", [])
        if not isinstance(products_raw, list):
            raise serializers.ValidationError({
                "products": ["Expected a list of products."]
            })
        attrs["products_input"] = products_raw

        return attrs

    def create(self, validated_data):
        customer = validated_data["customer_instance"]
        amount = validated_data["amount"]
        products_input = validated_data.get("products_input", [])

        with transaction.atomic():
            due = Due.objects.create(
                customer=customer,
                amount=amount,
                date=timezone.now().date(),
                is_edited=False,
            )

            linked_products = []
            for item in products_input:
                if isinstance(item, int):
                    prod = Product.objects.get(id=item)
                    linked_products.append(prod)
                elif isinstance(item, dict):
                    if "id" in item and len(item) == 1:
                        prod = Product.objects.get(id=item["id"])
                        linked_products.append(prod)
                    else:
                        prod_serializer = ProductSerializer(data=item)
                        prod_serializer.is_valid(raise_exception=True)
                        prod = prod_serializer.save()
                        linked_products.append(prod)

            if linked_products:
                due.products.set(linked_products)

        return due


class DepositSerializer(serializers.ModelSerializer):
    """
    Serializer for Deposit records.
    Handles recording a deposit for a customer belonging to the authenticated shopkeeper.
    date cannot be changed by the user.
    """
    customer_id = serializers.IntegerField(write_only=True, required=False)
    customer = CustomerListSerializer(read_only=True)
    date = serializers.DateField(read_only=True)

    class Meta:
        model = Deposit
        fields = [
            "id",
            "customer",
            "customer_id",
            "amount",
            "date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "date",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "amount": {"required": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        customer_id = attrs.get("customer_id")
        if customer_id is None and self.initial_data.get("customer") is not None:
            try:
                customer_id = int(self.initial_data["customer"])
            except (ValueError, TypeError):
                pass

        if customer_id is None:
            raise serializers.ValidationError({
                "customer_id": ["This field is required."]
            })

        if not user or not user.is_authenticated:
            raise serializers.ValidationError({
                "customer_id": ["Customer not found or does not belong to you."]
            })

        try:
            customer = Customer.objects.get(id=customer_id, user=user)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({
                "customer_id": ["Customer not found or does not belong to you."]
            })

        attrs["customer_instance"] = customer
        return attrs

    def create(self, validated_data):
        customer = validated_data["customer_instance"]
        amount = validated_data["amount"]

        return Deposit.objects.create(
            customer=customer,
            amount=amount,
            date=timezone.now().date(),
        )
