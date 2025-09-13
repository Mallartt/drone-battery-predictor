# urls.py
from django.contrib import admin
from django.urls import path
from application import views

urlpatterns = [
    path('drone_services', views.drone_services, name='drone_services'),
    path('drone_service/<int:id>/', views.drone_service, name='drone_service'),
    path("drone_battery_order/<int:order_id>/", views.drone_battery_order, name="drone_battery_order"),
]