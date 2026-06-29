from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        FARMER = "FARMER", "Farmer"
        HUB = "HUB", "Hub"
        RETAILER = "RETAILER", "Retailer"

    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices)
    location_name = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

class OTPVerification(models.Model):
    phone_number = models.CharField(max_length=20)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

class ProduceListing(models.Model):
    class Status(models.TextChoices):
        LISTED = "Listed", "Listed"
        MATCHED = "Matched", "Matched"
        PROCESSING = "Processing", "Processing"

    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="produce_listings", limit_choices_to={"role": User.Role.FARMER})
    crop_type = models.CharField(max_length=100)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    suggested_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LISTED)
    listed_on = models.DateTimeField(auto_now_add=True)

class HubInventory(models.Model):
    hub = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inventory", limit_choices_to={"role": User.Role.HUB})
    product_name = models.CharField(max_length=255)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=12, decimal_places=2)
    location = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now=True)

class Order(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "Order received", "Order received"
        ASSIGNED = "Assigned", "Assigned"
        PROCESSING = "Processing", "Processing"
        COMPLETED = "Completed", "Completed"

    produce = models.ForeignKey(ProduceListing, on_delete=models.CASCADE, related_name="orders")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders_placed", limit_choices_to={"role": User.Role.RETAILER})
    hub = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="orders_handled", null=True, blank=True, limit_choices_to={"role": User.Role.HUB})
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
