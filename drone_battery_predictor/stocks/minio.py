# minio.py
import uuid
import mimetypes
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, permissions
import boto3
from boto3.session import Config
from .models import DroneService

# S3 client для MinIO
s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{settings.AWS_S3_ENDPOINT_URL}" if not settings.MINIO_USE_SSL else f"https://{settings.AWS_S3_ENDPOINT_URL}",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1',  # для MinIO можно оставить любой
    config=Config(signature_version='s3v4')
)


class UploadDroneImage(APIView):
    """
    Загрузка изображения для услуги.
    POST /drone_services/<pk>/upload_image/
    Старое изображение удаляется из MinIO (если есть).
    Генерация уникального имени файла (uuid + исходное расширение).
    Сохраняется полный URL в service.image.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        service = get_object_or_404(DroneService, id=pk, is_deleted=False)
        file_obj = request.data.get('image')
        if not file_obj:
            return Response({"error": "Нет файла"}, status=status.HTTP_400_BAD_REQUEST)

        # Определяем расширение и генерируем уникальное имя
        ext = file_obj.name.split('.')[-1] if '.' in file_obj.name else 'bin'
        filename = f"{uuid.uuid4().hex}.{ext}"

        # Определяем content_type
        content_type, _ = mimetypes.guess_type(file_obj.name)
        if not content_type:
            content_type = 'application/octet-stream'

        # Удаляем старое изображение (если есть)
        if service.image:
            try:
                old_key = service.image.split('/')[-1]  # берём только имя файла
                s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=old_key)
            except Exception as e:
                print(f"[minio] Ошибка при удалении старого файла: {e}")

        # Загружаем новый файл с указанием content_type
        try:
            s3_client.upload_fileobj(
                file_obj,
                settings.AWS_STORAGE_BUCKET_NAME,
                filename,
                ExtraArgs={'ContentType': content_type}
            )
        except Exception as e:
            return Response({"error": f"Не удалось загрузить файл: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Сохраняем полный URL в модели
        protocol = "https" if settings.MINIO_USE_SSL else "http"
        service.image = f"{protocol}://{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{filename}"
        service.save(update_fields=['image'])

        return Response({"image": service.image}, status=status.HTTP_200_OK)
