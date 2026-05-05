from rest_framework import serializers

from .models import Order, ProduceListing, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone_number",
            "role",
            "location_name",
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "phone_number",
            "role",
            "location_name",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProduceListingSerializer(serializers.ModelSerializer):
    farmer = UserSerializer(read_only=True)

    class Meta:
        model = ProduceListing
        fields = (
            "id",
            "farmer",
            "crop_type",
            "quantity_kg",
            "suggested_price",
            "listed_on",
        )


class OrderSerializer(serializers.ModelSerializer):
    produce = ProduceListingSerializer(read_only=True)
    produce_id = serializers.PrimaryKeyRelatedField(
        source="produce",
        queryset=ProduceListing.objects.all(),
        write_only=True,
    )
    buyer = UserSerializer(read_only=True)
    hub = UserSerializer(read_only=True)
    hub_id = serializers.PrimaryKeyRelatedField(
        source="hub",
        queryset=User.objects.filter(role=User.Role.HUB),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "produce",
            "produce_id",
            "buyer",
            "hub",
            "hub_id",
            "quantity",
            "total_price",
            "status",
        )
        read_only_fields = ("status",)
