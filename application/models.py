from django.db import models
from django.contrib.auth.models import User  # встроенная таблица пользователей


class Service(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    discharge_rate = models.IntegerField(verbose_name='Расход энергии')
    image = models.CharField(max_length=255, null=True, blank=True, verbose_name='Изображение')
    category = models.CharField(max_length=255, verbose_name='Ценовая категория')
    power_multiplier = models.FloatField(verbose_name='Множитель мощности')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        DELETED = "DELETED", "Удалён"
        FORMED = "FORMED", "Сформирован"
        COMPLETED = "COMPLETED", "Завершён"
        REJECTED = "REJECTED", "Отклонён"

    creator = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    moderator = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders_moderated", null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
    )

    creation_datetime = models.DateTimeField(auto_now_add=True)
    formation_datetime = models.DateTimeField(blank=True, null=True)
    completion_datetime = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Заявка № {self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="orders")
    description = models.TextField(blank=True, null=True, verbose_name="Описание услуги в заявке")
    runtime = models.IntegerField(blank=True, null=True, verbose_name="Расчётное время (мин)")

    drone_weight = models.FloatField(blank=True, null=True, verbose_name="Масса дрона (кг)")
    cargo_weight = models.FloatField(blank=True, null=True, verbose_name="Масса груза (кг)")
    battery_capacity = models.IntegerField(blank=True, null=True, verbose_name="Ёмкость аккумулятора (mAh)")
    battery_voltage = models.FloatField(blank=True, null=True, verbose_name="Напряжение батареи (V)")
    efficiency = models.FloatField(blank=True, null=True, verbose_name="КПД")
    battery_remaining = models.FloatField(blank=True, null=True, verbose_name="Остаток заряда (%)")

    def __str__(self):
        return f"{self.service.name} в заявке № {self.order.id}"

    class Meta:
        unique_together = ('order', 'service')
