from rest_framework import viewsets, permissions, mixins
from rest_framework.exceptions import ValidationError, NotFound
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from .models import Due, Deposit
from .serializers import (
    DueSerializer,
    DueCreateSerializer,
    DepositSerializer,
    DepositCreateSerializer,
)
from customer.models import Customer


@extend_schema_view(
    list=extend_schema(
        summary="List dues for a customer",
        description="Retrieve all dues associated with a specific customer belonging to the authenticated shopkeeper. Requires customer_id query parameter.",
        tags=["Dues"],
        parameters=[
            OpenApiParameter(
                name="customer_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
                description="ID of the shopkeeper's customer whose dues to retrieve",
            )
        ],
        responses={200: DueSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Due detail",
        description="Retrieve details of a specific due record, including all itemized products.",
        tags=["Dues"],
        responses={200: DueSerializer},
    ),
    create=extend_schema(
        summary="Add Due",
        description=(
            "Record a new due balance for a customer. Provide customer_id, amount, and itemized product(s) "
            "in a single request. Products can be new product objects, existing product IDs (e.g. 1), or {\"id\": 1}. "
            "date and is_edited are automatic and cannot be altered. Dues cannot be edited or deleted once created."
        ),
        tags=["Dues"],
        request=DueCreateSerializer,
        responses={201: DueSerializer},
        examples=[
            OpenApiExample(
                "Add Due with New Products",
                value={
                    "customer_id": 1,
                    "amount": 220,
                    "products": [
                        {
                            "title": "Rice",
                            "quantity": 0.500,
                            "unit": "kg",
                            "price": 200,
                        },
                        {
                            "title": "Soap",
                            "quantity": 3,
                            "unit": "piece",
                            "price": 40,
                        },
                    ],
                },
                request_only=True,
            ),
            OpenApiExample(
                "Add Due with Existing Product ID",
                value={
                    "customer_id": 1,
                    "amount": 25,
                    "products": [{"id": 1}],
                },
                request_only=True,
            ),
        ],
    ),
)
class DueViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for recording and viewing Dues.
    Editing and deleting are strictly disallowed.
    Listing dues requires a customer_id query param for isolation.
    Restricted to authenticated shopkeepers.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DueSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Due.objects.none()

        user = self.request.user
        queryset = Due.objects.filter(customer__user=user).select_related("customer").prefetch_related("products")

        # When listing dues, require customer_id and verify customer ownership
        if self.action == "list":
            customer_param = self.request.query_params.get("customer_id") or self.request.query_params.get("customer")
            if not customer_param:
                raise ValidationError({"customer_id": ["customer_id query parameter is required."]})

            try:
                customer_id = int(customer_param)
            except (ValueError, TypeError):
                raise ValidationError({"customer_id": ["customer_id must be a valid integer."]})

            # Security: verify the customer exists and belongs to the authenticated user
            if not Customer.objects.filter(id=customer_id, user=user).exists():
                raise NotFound(detail="Customer not found.")

            queryset = queryset.filter(customer_id=customer_id)

        return queryset


@extend_schema_view(
    list=extend_schema(
        summary="List deposits",
        description="Retrieve deposits belonging to the authenticated shopkeeper's customers. Optionally filter by customer_id.",
        tags=["Deposits"],
        parameters=[
            OpenApiParameter(
                name="customer_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optional ID of the shopkeeper's customer whose deposits to retrieve",
            )
        ],
        responses={200: DepositSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Deposit detail",
        description="Retrieve details of a specific deposit record.",
        tags=["Deposits"],
        responses={200: DepositSerializer},
    ),
    create=extend_schema(
        summary="Add Deposit",
        description="Record a new deposit payment for a customer belonging to the authenticated shopkeeper. date is automatic and cannot be altered. Deposits cannot be edited or deleted once created.",
        tags=["Deposits"],
        request=DepositCreateSerializer,
        responses={201: DepositSerializer},
        examples=[
            OpenApiExample(
                "Add Deposit",
                value={
                    "customer_id": 1,
                    "amount": 200,
                },
                request_only=True,
            ),
        ],
    ),
)
class DepositViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for recording and viewing Deposits.
    Editing and deleting are strictly disallowed.
    Restricted to authenticated shopkeepers and their own customers.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DepositSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Deposit.objects.none()

        user = self.request.user
        queryset = Deposit.objects.filter(customer__user=user).select_related("customer")

        if self.action == "list":
            if "customer_id" in self.request.query_params:
                customer_param = self.request.query_params.get("customer_id")
            elif "customer" in self.request.query_params:
                customer_param = self.request.query_params.get("customer")
            else:
                customer_param = None

            if customer_param is not None:
                try:
                    customer_id = int(customer_param)
                except (ValueError, TypeError):
                    raise ValidationError({"customer_id": ["customer_id must be a valid integer."]})

                if not Customer.objects.filter(id=customer_id, user=user).exists():
                    raise NotFound(detail="Customer not found.")

                queryset = queryset.filter(customer_id=customer_id)

        return queryset
