from rest_framework import serializers
from .models import Customer


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing customers with name, phone_number, address, and total_due_amount.
    """
    total_due_amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone_number",
            "address",
            "total_due_amount",
        ]
        read_only_fields = ["id", "total_due_amount"]


class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed view, creation, and updating of customer details.
    total_due_amount is calculated dynamically and is strictly read-only.
    """
    total_due_amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone_number",
            "address",
            "total_due_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_due_amount",
            "created_at",
            "updated_at",
        ]
