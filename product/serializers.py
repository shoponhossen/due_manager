from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    """
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "quantity",
            "unit",
            "price",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "total_price", "created_at", "updated_at"]

    def to_internal_value(self, data):
        if isinstance(data, dict) and isinstance(data.get("unit"), str):
            data = data.copy()
            data["unit"] = data["unit"].strip().lower()
        return super().to_internal_value(data)

    @extend_schema_field(OpenApiTypes.NUMBER)
    def get_total_price(self, obj):
        return obj.total_price
