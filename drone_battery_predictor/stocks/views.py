# views.py
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from .models import DroneService, DroneBatteryOrder, DroneBatteryOrderItem
from django.contrib.auth.models import User
from .serializers import (
    DroneServiceSerializer,
    DroneOrderSerializer,
    DroneOrderItemSerializer,
    UserRegisterSerializer,
    UserSerializer
)
import boto3
from django.conf import settings
import uuid
from datetime import timedelta
from .minio import UploadDroneImage


# --------------------------
# Singleton-функция "фиксированного создателя"
# --------------------------
def get_fixed_creator():
    """
    Возвращает фиксированного пользователя-«создателя» с суперправами.
    username='admin', password='admin', is_superuser=True, is_staff=True.
    Если пользователь не существует — создаёт его.
    """
    username = 'admin'
    password = 'admin'
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
    return user


# S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{settings.AWS_S3_ENDPOINT_URL}",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1',
)


# ----------------------
# DRONE SERVICES
# ----------------------
class DroneServicesList(generics.ListCreateAPIView):
    serializer_class = DroneServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = DroneService.objects.filter(is_deleted=False)
        search = self.request.GET.get('drone_services_search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def perform_create(self, serializer):
        serializer.save()


class DroneServiceDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DroneServiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = DroneService.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        if instance.image:
            try:
                s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=instance.image)
            except Exception as e:
                print(f"[views] Ошибка при удалении файла из MinIO: {e}")
        instance.image = None
        instance.is_deleted = True
        instance.save(update_fields=['image', 'is_deleted'])


# ----------------------
# ADD DRONE SERVICE TO ORDER (Черновик)
# ----------------------
class AddToDroneOrder(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        service = get_object_or_404(DroneService, id=pk, is_deleted=False)
        creator = get_fixed_creator()
        order, created = DroneBatteryOrder.objects.get_or_create(
            creator=creator,
            status=DroneBatteryOrder.Status.DRAFT,
        )
        item, _ = DroneBatteryOrderItem.objects.get_or_create(drone_order=order, drone_service=service)
        serializer = DroneOrderItemSerializer(item)
        return Response({"order_id": order.id, "item": serializer.data})


# ----------------------
# DRONE ORDERS
# ----------------------
class DroneOrderBasketIcon(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        creator = get_fixed_creator()
        order = DroneBatteryOrder.objects.filter(
            creator=creator,
            status=DroneBatteryOrder.Status.DRAFT
        ).first()
        count = order.items.count() if order else 0
        return Response({"order_id": order.id if order else None, "count": count})


class DroneOrderList(generics.ListAPIView):
    serializer_class = DroneOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = DroneBatteryOrder.objects.exclude(
            status__in=[DroneBatteryOrder.Status.DELETED, DroneBatteryOrder.Status.DRAFT]
        )
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status_q = self.request.GET.get('status')
        if date_from:
            qs = qs.filter(formed_at__gte=date_from)
        if date_to:
            qs = qs.filter(formed_at__lte=date_to)
        if status_q:
            qs = qs.filter(status=status_q)
        return qs.select_related('creator', 'moderator').prefetch_related('items__drone_service')


class DroneOrderDetailView(generics.RetrieveAPIView):
    serializer_class = DroneOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DroneBatteryOrder.objects.all()


class DroneOrderUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        creator = get_fixed_creator()
        if order.creator != creator and not request.user.is_staff:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)

        forbidden = {'id', 'creator', 'moderator', 'status', 'created_at', 'formed_at', 'completed_at'}
        for field, value in request.data.items():
            if field in forbidden:
                continue
            if hasattr(order, field):
                setattr(order, field, value)
        order.save()
        serializer = DroneOrderSerializer(order)
        return Response(serializer.data)


class DroneOrderForm(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        creator = get_fixed_creator()
        if order.creator != creator:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)
        if order.status != DroneBatteryOrder.Status.DRAFT:
            return Response({"error": "Можно формировать только черновик"}, status=status.HTTP_400_BAD_REQUEST)

        required_fields = ['drone_weight', 'cargo_weight', 'battery_capacity', 'battery_voltage', 'efficiency', 'battery_remaining']
        for f in required_fields:
            if getattr(order, f, None) is None:
                return Response({"error": f"Не заполнено поле {f}"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = DroneBatteryOrder.Status.FORMED
        order.formed_at = timezone.now()
        order.save()
        return Response({"status": "ok", "formed_at": order.formed_at}, status=status.HTTP_200_OK)


class DroneOrderComplete(APIView):
    permission_classes = [permissions.IsAdminUser]

    def put(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        if order.status != DroneBatteryOrder.Status.FORMED:
            return Response({"error": "Можно обрабатывать только сформированную заявку"}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action')
        if action == 'complete':
            order.status = DroneBatteryOrder.Status.COMPLETED
            order.moderator = request.user
            order.completed_at = timezone.now()
            computed_cost = sum((item.drone_service.power_multiplier * (item.runtime or 0) * 10) for item in order.items.all())
            delivery_date = timezone.now() + timedelta(days=30)
            order.save()
            return Response({
                "status": "ok",
                "order_status": order.status,
                "computed_cost": computed_cost,
                "delivery_date": delivery_date
            }, status=status.HTTP_200_OK)
        elif action == 'reject':
            order.status = DroneBatteryOrder.Status.REJECTED
            order.moderator = request.user
            order.completed_at = timezone.now()
            order.save()
            return Response({"status": "ok", "order_status": order.status}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Неверное действие"}, status=status.HTTP_400_BAD_REQUEST)


class DroneOrderDelete(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        creator = get_fixed_creator()
        if order.creator != creator and not request.user.is_staff:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)
        order.status = DroneBatteryOrder.Status.DELETED
        order.save()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


# ----------------------
# DRONE ORDER ITEMS
# ----------------------
class DroneOrderItemUpdate(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        item = get_object_or_404(DroneBatteryOrderItem, id=pk)
        creator = get_fixed_creator()
        if item.drone_order.creator != creator and not request.user.is_staff:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)

        forbidden = {'id', 'drone_order', 'drone_service'}
        for field, value in request.data.items():
            if field in forbidden:
                continue
            if hasattr(item, field):
                setattr(item, field, value)
        item.save()
        serializer = DroneOrderItemSerializer(item)
        return Response(serializer.data)


class DroneOrderItemDelete(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(DroneBatteryOrderItem, id=pk)
        creator = get_fixed_creator()
        if item.drone_order.creator != creator and not request.user.is_staff:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)
        item.delete()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


# ----------------------
# USERS
# ----------------------
class UserRegister(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "ok"}, status=status.HTTP_201_CREATED)


class UserDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserLogin(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


class UserLogout(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"status": "ok"})
