from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Product
from .serializers import ProductSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Retrieve all products.",
        tags=["Products"],
        responses={200: ProductSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Product detail",
        description="Retrieve a specific product.",
        tags=["Products"],
        responses={200: ProductSerializer},
    ),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet for Product catalogue.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
