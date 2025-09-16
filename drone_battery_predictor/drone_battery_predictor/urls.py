# urls.py
from django.urls import path
from stocks import views
from django.contrib import admin

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Drone services
    path('drone_services/', views.DroneServicesList.as_view(), name='drone-services-list'),
    path('drone_services/<int:pk>/', views.DroneServiceDetail.as_view(), name='drone-service-detail'),
    path('drone_services/<int:pk>/add_to_order/', views.AddToDroneOrder.as_view(), name='drone-service-add-to-order'),
    path('drone_services/<int:pk>/upload_image/', views.UploadDroneImage.as_view(), name='drone-service-upload-image'),

    # Drone orders
    path('drone_orders/basket_icon/', views.DroneOrderBasketIcon.as_view(), name='drone-order-basket-icon'),
    path('drone_orders/', views.DroneOrderList.as_view(), name='drone-orders-list'),
    path('drone_orders/<int:pk>/', views.DroneOrderDetailView.as_view(), name='drone-order-detail'),
    path('drone_orders/<int:pk>/update/', views.DroneOrderUpdate.as_view(), name='drone-order-update'),
    path('drone_orders/<int:pk>/form/', views.DroneOrderForm.as_view(), name='drone-order-form'),
    path('drone_orders/<int:pk>/complete/', views.DroneOrderComplete.as_view(), name='drone-order-complete'),
    path('drone_orders/<int:pk>/delete/', views.DroneOrderDelete.as_view(), name='drone-order-delete'),

    # Drone items (m-m)
    path('drone_items/<int:pk>/update/', views.DroneOrderItemUpdate.as_view(), name='drone-item-update'),
    path('drone_items/<int:pk>/delete/', views.DroneOrderItemDelete.as_view(), name='drone-item-delete'),

    # Drone users
    path('drone_users/register/', views.UserRegister.as_view(), name='drone-user-register'),
    path('drone_users/me/', views.UserDetail.as_view(), name='drone-user-me'),
    path('drone_users/login/', views.UserLogin.as_view(), name='drone-user-login'),
    path('drone_users/logout/', views.UserLogout.as_view(), name='drone-user-logout'),
]
