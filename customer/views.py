from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

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
        description="Add a new customer under the authenticated shopkeeper.",
        tags=["Customers"],
        request=CustomerDetailSerializer,
        responses={201: CustomerDetailSerializer},
    ),
    update=extend_schema(
        summary="Update customer details",
        description="Update customer details (name, phone_number, address). Note: total_due_amount is strictly read-only.",
        tags=["Customers"],
        request=CustomerDetailSerializer,
        responses={200: CustomerDetailSerializer},
    ),
    partial_update=extend_schema(
        summary="Partially update customer details",
        description="Partially update customer details (name, phone_number, address). Note: total_due_amount is strictly read-only.",
        tags=["Customers"],
        request=CustomerDetailSerializer,
        responses={200: CustomerDetailSerializer},
    ),
    destroy=extend_schema(
        summary="Delete customer",
        description="Delete a customer and all their associated dues and deposits.",
        tags=["Customers"],
        responses={204: OpenApiResponse(description="Customer deleted successfully")},
    ),
)
class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CRUD operations on Customer.
    Restricted to authenticated shopkeepers and their own customers.
    """
    permission_classes = [permissions.IsAuthenticated]

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
