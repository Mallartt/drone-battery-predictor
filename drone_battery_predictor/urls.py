from django.contrib import admin
from django.urls import path
from application import views

urlpatterns = [
    path('', views.services_list, name='services_list'),
    path('service/<int:id>/', views.service_detail, name='service_detail'),
    path('order/', views.order_detail, name='order_detail'),
]