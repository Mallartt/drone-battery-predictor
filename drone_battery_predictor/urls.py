from django.contrib import admin
from django.urls import path
from application import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('drone_services', views.drone_services, name='drone_services'),
    path('drone_service/<int:id>/', views.drone_service, name='drone_service'),
    path("drone_battery_order/<int:order_id>/", views.drone_order_detail, name="drone_order_detail"),
    path("drone_battery_order/add/<int:service_id>/", views.add_to_drone_order, name="add_to_drone_order"),
    path("drone_battery_order/delete/<int:order_id>/", views.delete_drone_order, name="delete_drone_order"),
]
