from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DroneService, DroneBatteryOrder, DroneBatteryOrderItem

class DroneServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = DroneService
        fields = ['id', 'name', 'description', 'power_multiplier', 'image']
        read_only_fields = ['id', 'image']

    def get_image(self, obj):
        return obj.image if obj.image else None


class DroneOrderItemSerializer(serializers.ModelSerializer):
    drone_service_detail = DroneServiceSerializer(source='drone_service', read_only=True)
    drone_service = serializers.PrimaryKeyRelatedField(
        queryset=DroneService.objects.filter(is_deleted=False)
    )
    drone_order = serializers.PrimaryKeyRelatedField(
        queryset=DroneBatteryOrder.objects.all()
    )

    class Meta:
        model = DroneBatteryOrderItem
        fields = [
            'id',
            'drone_order',
            'drone_service',
            'drone_service_detail',
            'runtime',
            'wind_multiplier',
            'rain_multiplier',
        ]
        read_only_fields = ['id', 'drone_service_detail']

    def update(self, instance, validated_data):
        validated_data.pop('drone_service', None)
        return super().update(instance, validated_data)


class DroneOrderSerializer(serializers.ModelSerializer):
    items = DroneOrderItemSerializer(many=True, read_only=True)
    creator = serializers.CharField(source='creator.username', read_only=True)
    moderator = serializers.CharField(source='moderator.username', read_only=True)

    class Meta:
        model = DroneBatteryOrder
        fields = [
            'id',
            'creator',
            'moderator',
            'status',
            'created_at',
            'formed_at',
            'completed_at',
            'items',
            'drone_weight',
            'cargo_weight',
            'battery_capacity',
            'battery_voltage',
            'efficiency',
            'battery_remaining'
        ]
        read_only_fields = ['id', 'creator', 'moderator', 'status', 'created_at', 'formed_at', 'completed_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
