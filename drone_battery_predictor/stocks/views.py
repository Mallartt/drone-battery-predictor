# views.py
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from datetime import timedelta
import boto3, uuid
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token  
from .models import DroneService, DroneBatteryOrder, DroneBatteryOrderItem
from .serializers import (
    DroneServiceSerializer,
    DroneOrderSerializer,
    DroneOrderItemSerializer,
    UserRegisterSerializer,
    UserSerializer      
)
import math

def get_fixed_creator():
    username = 'admin'
    password = 'admin'
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
    return user


s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{settings.AWS_S3_ENDPOINT_URL}",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1',
)


class DroneServicesList(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = DroneService.objects.filter(is_deleted=False)
        search = request.GET.get('drone_services_search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        serializer = DroneServiceSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DroneServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DroneServiceDetail(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        service = get_object_or_404(DroneService, id=pk, is_deleted=False)
        serializer = DroneServiceSerializer(service)
        return Response(serializer.data)

    def put(self, request, pk):
        service = get_object_or_404(DroneService, id=pk, is_deleted=False)
        serializer = DroneServiceSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        service = get_object_or_404(DroneService, id=pk, is_deleted=False)
        if service.image:
            try:
                s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=service.image)
            except Exception as e:
                print(f"[views] Ошибка при удалении файла из MinIO: {e}")
        service.image = None
        service.is_deleted = True
        service.save(update_fields=['image', 'is_deleted'])
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class AddToDroneOrder(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        service = get_object_or_404(DroneService, id=pk, is_deleted=False)
        creator = get_fixed_creator()
        order, _ = DroneBatteryOrder.objects.get_or_create(
            creator=creator,
            status=DroneBatteryOrder.Status.DRAFT,
        )
        item, _ = DroneBatteryOrderItem.objects.get_or_create(drone_order=order, drone_service=service)
        serializer = DroneOrderItemSerializer(item)
        return Response({"order_id": order.id, "item": serializer.data})


class UploadDroneImage(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        service = get_object_or_404(DroneService, id=pk, is_deleted=False)
        file_obj = request.data.get('image')
        if not file_obj:
            return Response({"error": "Нет файла"}, status=status.HTTP_400_BAD_REQUEST)

        ext = file_obj.name.split('.')[-1] if '.' in file_obj.name else 'bin'
        filename = f"{uuid.uuid4().hex}.{ext}"

        import mimetypes
        content_type, _ = mimetypes.guess_type(file_obj.name)
        if not content_type:
            content_type = 'application/octet-stream'

        if service.image:
            try:
                old_key = service.image.split('/')[-1] 
                s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=old_key)
            except Exception as e:
                print(f"[views] Ошибка при удалении старого файла: {e}")

        try:
            s3_client.upload_fileobj(
                file_obj,
                settings.AWS_STORAGE_BUCKET_NAME,
                filename,
                ExtraArgs={'ContentType': content_type}
            )
        except Exception as e:
            return Response({"error": f"Не удалось загрузить файл: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        protocol = "https" if getattr(settings, "MINIO_USE_SSL", False) else "http"
        service.image = f"{protocol}://{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{filename}"
        service.save(update_fields=['image'])

        return Response({"image": service.image}, status=status.HTTP_200_OK)



class DroneOrderBasketIcon(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        creator = get_fixed_creator()
        order = DroneBatteryOrder.objects.filter(
            creator=creator,
            status=DroneBatteryOrder.Status.DRAFT
        ).first()
        count = order.items.count() if order else 0
        return Response({"order_id": order.id if order else None, "count": count})


class DroneOrderList(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = DroneBatteryOrder.objects.exclude(
            status__in=[DroneBatteryOrder.Status.DELETED, DroneBatteryOrder.Status.DRAFT]
        )
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        status_q = request.GET.get('status')
        if date_from:
            qs = qs.filter(formed_at__gte=date_from)
        if date_to:
            qs = qs.filter(formed_at__lte=date_to)
        if status_q:
            qs = qs.filter(status=status_q)
        serializer = DroneOrderSerializer(qs, many=True)
        return Response(serializer.data)


class DroneOrderDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        serializer = DroneOrderSerializer(order)
        return Response(serializer.data)


class DroneOrderUpdate(APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        creator = get_fixed_creator()
        if order.creator != creator:
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
    permission_classes = [permissions.AllowAny]

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
    permission_classes = [permissions.AllowAny]

    def put(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        
        if order.status != DroneBatteryOrder.Status.FORMED:
            return Response({"error": "Можно обрабатывать только сформированную заявку"}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action')
        if action not in ['complete', 'reject']:
            return Response({"error": "Неверное действие"}, status=status.HTTP_400_BAD_REQUEST)

        creator = get_fixed_creator()

        if action == 'complete':
            mass_drone = order.drone_weight or 0
            mass_payload = order.cargo_weight or 0
            battery_capacity_mAh = order.battery_capacity or 0
            battery_voltage = order.battery_voltage or 0
            efficiency = order.efficiency or 1.0
            battery_level_pct = order.battery_remaining or 0

            battery_level = battery_level_pct / 100
            energy_Wh = battery_capacity_mAh * battery_voltage / 1000 * battery_level * efficiency

            for item in order.items.all():
                multiplier = getattr(item.drone_service, "power_multiplier", 1.0) or 1.0
                wind_coeff = getattr(item, "wind_multiplier", 1.0) or 1.0
                rain_coeff = getattr(item, "rain_multiplier", 1.0) or 1.0

                total_mass = mass_drone + mass_payload
                power_W = multiplier * math.pow(total_mass, 1.5) * wind_coeff * rain_coeff
                item.runtime = round((energy_Wh / power_W) * 60) if power_W > 0 else 0
                item.save()

            delivery_date = timezone.now() + timedelta(days=30)

            order.status = DroneBatteryOrder.Status.COMPLETED
            order.moderator = creator
            order.completed_at = timezone.now()
            order.save()

            return Response({
                "status": "ok",
                "order_status": order.status,
                "delivery_date": delivery_date
            }, status=status.HTTP_200_OK)

        elif action == 'reject':
            order.status = DroneBatteryOrder.Status.REJECTED
            order.moderator = creator
            order.completed_at = timezone.now()
            order.save()
            return Response({"status": "ok", "order_status": order.status}, status=status.HTTP_200_OK)
        
class DroneOrderDelete(APIView):
    permission_classes = [permissions.AllowAny]

    def delete(self, request, pk):
        order = get_object_or_404(DroneBatteryOrder, id=pk)
        creator = get_fixed_creator()
        if order.creator != creator:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)
        order.status = DroneBatteryOrder.Status.DELETED
        order.save()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class DroneOrderItemUpdate(APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request, pk):
        item = get_object_or_404(DroneBatteryOrderItem, id=pk)
        creator = get_fixed_creator()
        if item.drone_order.creator != creator:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)

        serializer = DroneOrderItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



class DroneOrderItemDelete(APIView):
    permission_classes = [permissions.AllowAny]

    def delete(self, request, pk):
        item = get_object_or_404(DroneBatteryOrderItem, id=pk)
        creator = get_fixed_creator()
        if item.drone_order.creator != creator:
            return Response({"error": "Нет прав"}, status=status.HTTP_403_FORBIDDEN)
        item.delete()
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class UserRegister(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"status": "ok"}, status=status.HTTP_201_CREATED)



CURRENT_USER = None


class UserLogin(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        global CURRENT_USER
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        CURRENT_USER = user
        return Response({"status": "ok"})


class UserDetail(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        global CURRENT_USER
        if not CURRENT_USER:
            return Response({"error": "Нет активного пользователя"}, status=401)
        serializer = UserSerializer(CURRENT_USER)
        return Response(serializer.data)

    def put(self, request):
        global CURRENT_USER
        if not CURRENT_USER:
            return Response({"error": "Нет активного пользователя"}, status=401)
        serializer = UserSerializer(CURRENT_USER, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserLogout(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        global CURRENT_USER
        CURRENT_USER = None
        return Response({"status": "ok"})
