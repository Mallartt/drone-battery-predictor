# models.py 
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField


class DroneService(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.CharField(max_length=255, null=True, blank=True)
    power_multiplier = models.FloatField(default=1.0)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class DroneBatteryOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        DELETED = "DELETED", "Удалён"
        FORMED = "FORMED", "Сформирован"
        COMPLETED = "COMPLETED", "Завершён"
        REJECTED = "REJECTED", "Отклонён"

    
    creator = models.ForeignKey(User, on_delete=models.PROTECT)
    moderator = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders_moderated", null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    drone_weight = models.FloatField(null=True, blank=True)
    cargo_weight = models.FloatField(null=True, blank=True)
    battery_capacity = models.FloatField(null=True, blank=True)
    battery_voltage = models.FloatField(null=True, blank=True)
    efficiency = models.FloatField(null=True, blank=True)
    battery_remaining = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Заявка {self.id} ({self.status})"


class DroneBatteryOrderItem(models.Model):
    drone_order = models.ForeignKey(DroneBatteryOrder, on_delete=models.PROTECT, related_name="items")
    drone_service = models.ForeignKey(DroneService, on_delete=models.PROTECT, related_name="orders")
    runtime = models.FloatField(null=True, blank=True)
    wind_multiplier = models.FloatField(null=True, blank=True)
    rain_multiplier = models.FloatField(null=True, blank=True)


    def __str__(self):
        return f"{self.drone_service.name} в заявке {self.drone_order.id}"


    class Meta:
        unique_together = ("drone_order", "drone_service")