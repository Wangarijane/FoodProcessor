from decimal import Decimal

from django.db.models import Sum
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, ProduceListing, User
from .serializers import (
    OrderSerializer,
    ProduceListingSerializer,
    UserRegistrationSerializer,
)


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserRegistrationSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class ProduceListingViewSet(viewsets.ModelViewSet):
    serializer_class = ProduceListingSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = ProduceListing.objects.select_related("farmer").order_by("-listed_on")
        if self.request.user.role == User.Role.FARMER:
            return queryset.filter(farmer=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.FARMER:
            return Response(
                {"detail": "Only farmers can create produce listings."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.select_related("produce", "produce__farmer", "buyer", "hub")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.order_by("-id")
        if user.role == User.Role.RETAILER:
            return queryset.filter(buyer=user)
        if user.role == User.Role.FARMER:
            return queryset.filter(produce__farmer=user)
        if user.role == User.Role.HUB:
            return queryset.filter(hub=user)
        return queryset.none()

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.RETAILER:
            return Response(
                {"detail": "Only retailers can place orders."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user, status=Order.Status.PENDING)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        if request.user.role != User.Role.HUB:
            return Response(
                {"detail": "Only hubs can update order status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")
        allowed_statuses = {Order.Status.PROCESSING, Order.Status.COMPLETED}
        if new_status not in allowed_statuses:
            return Response(
                {"detail": "Status must be Processing or Completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        if order.hub_id is None:
            order.hub = request.user
        order.save(update_fields=["status", "hub"])
        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)


class FarmerEarningsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.FARMER:
            return Response(
                {"detail": "Only farmers can view earnings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        earnings = (
            Order.objects.filter(
                produce__farmer=request.user,
                status=Order.Status.COMPLETED,
            ).aggregate(total=Sum("total_price"))["total"]
            or Decimal("0.00")
        )
        return Response({"farmer_id": request.user.id, "total_earnings": earnings})
