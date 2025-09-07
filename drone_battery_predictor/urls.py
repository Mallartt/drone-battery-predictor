from django.contrib import admin
from django.urls import path
from application import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.services_list, name='services_list'),
    path('service/<int:id>/', views.service_detail, name='service_detail'),
    path('order/', views.order_detail, name='order_detail'),
    path('order/add/<int:service_id>/', views.add_to_order, name='add_to_order'),
    path('order/delete/<int:order_id>/', views.delete_order, name='delete_order'),
]
