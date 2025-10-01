from django.contrib import admin
from .models import DroneService, DroneBatteryOrder, DroneBatteryOrderItem

admin.site.register(DroneService)
admin.site.register(DroneBatteryOrder)
admin.site.register(DroneBatteryOrderItem)
