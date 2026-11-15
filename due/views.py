from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Due
from .serializers import DueSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List dues",
        description="Retrieve all dues recorded for the authenticated shopkeeper's customers.",
        tags=["Dues"],
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
        description="Record a new due balance for a customer. Provide customer_id, amount, and itemized product(s) in a single request. date is automatically assigned and is_edited cannot be altered by the user.",
        tags=["Dues"],
        request=DueSerializer,
        responses={201: DueSerializer},
    ),
    destroy=extend_schema(
        summary="Delete due",
        description="Delete a due entry.",
        tags=["Dues"],
        responses={204: OpenApiResponse(description="Due deleted successfully")},
    ),
)
class DueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for recording and viewing Dues.
    Restricted to authenticated shopkeepers.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DueSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Due.objects.none()
        return Due.objects.filter(customer__user=self.request.user).select_related("customer").prefetch_related("products")
