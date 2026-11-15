from rest_framework import viewsets, permissions, mixins
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Customer
from .serializers import CustomerListSerializer, CustomerDetailSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List customers",
        description="Retrieve a list of customers belonging to the authenticated shopkeeper with name, phone number, and current total due amount.",
        tags=["Customers"],
        responses={200: CustomerListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Customer detail",
        description="Retrieve full details for a specific customer, including address and total due amount.",
        tags=["Customers"],
        responses={200: CustomerDetailSerializer},
    ),
    create=extend_schema(
        summary="Create customer",
        description="Add a new customer under the authenticated shopkeeper. Note: customers cannot be edited or deleted once created.",
        tags=["Customers"],
        request=CustomerDetailSerializer,
        responses={201: CustomerDetailSerializer},
    ),
)
class CustomerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for Customer operations (Create, List, Retrieve).
    Editing and Deleting are strictly disallowed.
    Restricted to authenticated shopkeepers and their own customers.
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        # Multi-tenancy: Only return customers belonging to the logged-in user
        if getattr(self, "swagger_fake_view", False):
            return Customer.objects.none()
        return Customer.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return CustomerListSerializer
        return CustomerDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
