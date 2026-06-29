from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from random import randint
from django.db.models import Sum
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPVerification, Order, ProduceListing, User, HubInventory
from .serializers import (
    UserRegistrationSerializer, ProduceListingSerializer, OrderSerializer, HubInventorySerializer,
    AppListingSerializer, AppFarmerOrderSerializer, AppMarketItemSerializer, AppHubOrderSerializer,
    get_emoji_for_crop
)

class RegistrationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserRegistrationSerializer(user).data, status=status.HTTP_201_CREATED)

class SendOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone_number = request.data.get("phone_number")
        if not phone_number:
            return Response({"detail": "phone_number is required."}, status=status.HTTP_400_BAD_REQUEST)
        otp_code = f"{randint(0, 999999):06d}"
        OTPVerification.objects.create(phone_number=phone_number, otp_code=otp_code)
        return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone_number = request.data.get("phone_number")
        otp = request.data.get("otp")
        if not phone_number or not otp:
            return Response({"detail": "phone_number and otp are required."}, status=status.HTTP_400_BAD_REQUEST)

        otp_record = OTPVerification.objects.filter(phone_number=phone_number, otp_code=otp).order_by("-created_at").first()
        if otp_record is None:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number=phone_number).first()
        if user is None:
            return Response({"is_new_user": True}, status=status.HTTP_200_OK)

        refresh = RefreshToken.for_user(user)
        return Response({
            "is_new_user": False,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)

class SuggestedPriceView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        prices = {"Tomatoes": 500, "Maize": 320, "Peppers": 650, "Cassava": 280, "Yam": 700, "Beans": 900}
        return Response(prices, status=status.HTTP_200_OK)

class ProduceListingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AppListingSerializer
        return ProduceListingSerializer

    def get_queryset(self):
        queryset = ProduceListing.objects.select_related("farmer").order_by("-listed_on")
        if self.request.user.role == User.Role.FARMER:
            return queryset.filter(farmer=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)

class HubInventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AppMarketItemSerializer
        return HubInventorySerializer

    def get_queryset(self):
        return HubInventory.objects.all().order_by("-last_updated")

    def perform_create(self, serializer):
        serializer.save(hub=self.request.user)

class OrderViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.select_related("produce", "produce__farmer", "buyer", "hub")

    def get_serializer_class(self):
        if self.request.method == 'GET':
            user = self.request.user
            if user.role == User.Role.FARMER:
                return AppFarmerOrderSerializer
            if user.role == User.Role.HUB:
                return AppHubOrderSerializer
        return OrderSerializer

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
            return Response({"detail": "Only retailers can place orders."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        produce = serializer.validated_data['produce']
        quantity = serializer.validated_data['quantity']

        # LOGIC FIX 1: Inventory Checking
        if produce.quantity_kg < quantity:
            raise ValidationError({"detail": f"Only {produce.quantity_kg}kg available."})

        # LOGIC FIX 2: Inventory Depletion
        produce.quantity_kg -= quantity
        
        # If inventory hits 0, auto-update the status so it disappears from the marketplace
        if produce.quantity_kg == 0:
            produce.status = ProduceListing.Status.MATCHED
        produce.save()

        # LOGIC FIX 3: Secure Server-Side Pricing (Ignore client's total_price)
        secure_total = produce.suggested_price * quantity

        # Save order securely
        serializer.save(
            buyer=self.request.user, 
            total_price=secure_total, 
            status=Order.Status.RECEIVED
        )

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        
        if request.user.role != User.Role.HUB:
            return Response({"detail": "Only hubs can update order status."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get("status")

        # LOGIC FIX 4: Strict State Machine logic
        # Defines exactly what the NEXT allowed step is
        valid_transitions = {
            Order.Status.RECEIVED: [Order.Status.ASSIGNED, Order.Status.PROCESSING],
            Order.Status.ASSIGNED: [Order.Status.PROCESSING],
            Order.Status.PROCESSING: [Order.Status.COMPLETED],
        }

        allowed_next_steps = valid_transitions.get(order.status, [])
        
        if new_status not in allowed_next_steps:
            return Response(
                {"detail": f"Invalid transition. Cannot move from '{order.status}' to '{new_status}'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        if order.hub_id is None:
            order.hub = request.user
            
        order.save(update_fields=["status", "hub", "updated_at"])
        return Response({"detail": f"Status successfully updated to {new_status}"}, status=status.HTTP_200_OK)


class FarmerEarningsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.FARMER:
            return Response({"detail": "Only farmers can view earnings."}, status=status.HTTP_403_FORBIDDEN)

        completed_orders = Order.objects.filter(
            produce__farmer=request.user, 
            status=Order.Status.COMPLETED
        ).order_by("-updated_at")

        total = completed_orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")
        
        now = timezone.now()
        week_earnings = completed_orders.filter(updated_at__gte=now - timedelta(days=7)).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")
        month_earnings = completed_orders.filter(updated_at__gte=now - timedelta(days=30)).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

        payments = [
            {
                "crop": order.produce.crop_type,
                "emoji": get_emoji_for_crop(order.produce.crop_type),
                "qty": int(order.quantity),
                "amount": int(order.total_price),
                "date": order.updated_at.strftime("%d %b %Y")
            } for order in completed_orders
        ]

        return Response({
            "totalEarnings": int(total),
            "weekEarnings": int(week_earnings),
            "monthEarnings": int(month_earnings),
            "payments": payments
        }, status=status.HTTP_200_OK)
