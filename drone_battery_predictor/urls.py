from django.contrib import admin
from django.urls import path
from application import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.services_list, name="services_list"),
    path("drone_services/<int:id>/", views.service_detail, name="service_detail"),
    path("drone_battery_orderitem/<int:order_id>/", views.order_detail, name="order_detail"),
    path("drone_battery_orderitem/add/<int:service_id>/", views.add_to_order, name="add_to_order"),
    path("drone_battery_orderitem/delete/<int:order_id>/", views.delete_order, name="delete_order"),
]
