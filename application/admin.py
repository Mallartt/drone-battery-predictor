from django.contrib import admin

from .models import DroneMode, DroneOrder, DroneOrderItem

admin.site.register(DroneMode)
admin.site.register(DroneOrder)
admin.site.register(DroneOrderItem)