from django.contrib import admin

from .models import Service, Order, OrderItem

admin.site.register(Service)
admin.site.register(Order)
admin.site.register(OrderItem)