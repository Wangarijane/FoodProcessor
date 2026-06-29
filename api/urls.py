from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    FarmerEarningsView, OrderViewSet, ProduceListingViewSet, RegistrationView, 
    SendOTPView, VerifyOTPView, HubInventoryViewSet, SuggestedPriceView
)

router = DefaultRouter()
router.register("produce", ProduceListingViewSet, basename="produce")
router.register("orders", OrderViewSet, basename="orders")
router.register("hub-inventory", HubInventoryViewSet, basename="hub-inventory")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegistrationView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("farmer/earnings/", FarmerEarningsView.as_view(), name="farmer-earnings"),
    path("prices/suggested/", SuggestedPriceView.as_view(), name="suggested-prices"),
]
