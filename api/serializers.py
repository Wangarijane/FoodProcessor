from rest_framework import serializers
from .models import Order, ProduceListing, User, HubInventory

CROP_EMOJI = {
    'Tomatoes': '🍅', 'Maize': '🌽', 'Peppers': '🌶️',
    'Cassava': '🍠', 'Yam': '🥔', 'Beans': '🫘',
    'Tomato Paste': '🍅', 'Maize Flour': '🌽',
    'Dried Pepper': '🌶️', 'Cassava Flour': '🍠',
}

def get_emoji_for_crop(crop_name):
    return CROP_EMOJI.get(crop_name, '🌱')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "phone_number", "role", "location_name")

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "password", "first_name", "phone_number", "role", "location_name")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class ProduceListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduceListing
        fields = "__all__"

class HubInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HubInventory
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

# --- App-Matched Serializers for GET requests ---

class AppListingSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='crop_type', read_only=True)
    qty = serializers.IntegerField(source='quantity_kg', read_only=True)
    price = serializers.IntegerField(source='suggested_price', read_only=True)
    emoji = serializers.SerializerMethodField()

    class Meta:
        model = ProduceListing
        fields = ("id", "name", "emoji", "qty", "price", "status")

    def get_emoji(self, obj):
        return get_emoji_for_crop(obj.crop_type)

class AppFarmerOrderSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    crop = serializers.CharField(source='produce.crop_type', read_only=True)
    qty = serializers.IntegerField(source='quantity', read_only=True)
    hub = serializers.CharField(source='hub.first_name', default="Unassigned", read_only=True)
    step = serializers.SerializerMethodField()
    emoji = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "crop", "emoji", "qty", "hub", "step")

    def get_step(self, obj):
        steps = {"Order received": 1, "Assigned": 2, "Processing": 3, "Completed": 4}
        return steps.get(obj.status, 1)

    def get_emoji(self, obj):
        return get_emoji_for_crop(obj.produce.crop_type)

class AppMarketItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='product_name', read_only=True)
    qty = serializers.IntegerField(source='quantity_kg', read_only=True)
    price = serializers.IntegerField(source='price_per_kg', read_only=True)
    hub = serializers.CharField(source='hub.first_name', read_only=True)
    emoji = serializers.SerializerMethodField()

    class Meta:
        model = HubInventory
        fields = ("id", "name", "emoji", "hub", "location", "price", "qty")

    def get_emoji(self, obj):
        return get_emoji_for_crop(obj.product_name)

class AppHubOrderSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    product = serializers.CharField(source='produce.crop_type', read_only=True)
    qty = serializers.IntegerField(source='quantity', read_only=True)
    store = serializers.CharField(source='buyer.first_name', default="Unknown Store", read_only=True)
    total = serializers.IntegerField(source='total_price', read_only=True)
    emoji = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "product", "emoji", "qty", "store", "total", "status")

    def get_emoji(self, obj):
        return get_emoji_for_crop(obj.produce.crop_type)
