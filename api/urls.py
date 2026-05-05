from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import FarmerEarningsView, OrderViewSet, ProduceListingViewSet, RegistrationView

router = DefaultRouter()
router.register("produce", ProduceListingViewSet, basename="produce")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", RegistrationView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("farmer/earnings/", FarmerEarningsView.as_view(), name="farmer-earnings"),
]
