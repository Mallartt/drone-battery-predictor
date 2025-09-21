# urls.py
from django.urls import path, re_path
from stocks import views
from django.contrib import admin
from rest_framework import permissions as drf_permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Drone Battery Predictor API",
      default_version='v1',
      description="API для заявок на расчёт времени полёта дрона",
   ),
   public=True,
   permission_classes=(drf_permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path('drone_services/', views.DroneServicesList.as_view(), name='drone-services-list'),
    path('drone_services/<int:pk>/', views.DroneServiceDetail.as_view(), name='drone-service-detail'),
    path('drone_services/<int:pk>/add_to_order/', views.AddToDroneOrder.as_view(), name='drone-service-add-to-order'),
    path('drone_services/<int:pk>/upload_image/', views.UploadDroneImage.as_view(), name='drone-service-upload-image'),

    path('drone_orders/basket_icon/', views.DroneOrderBasketIcon.as_view(), name='drone-order-basket-icon'),
    path('drone_orders/', views.DroneOrderList.as_view(), name='drone-orders-list'),
    path('drone_orders/<int:pk>/', views.DroneOrderDetailView.as_view(), name='drone-order-detail'),
    path('drone_orders/<int:pk>/update/', views.DroneOrderUpdate.as_view(), name='drone-order-update'),
    path('drone_orders/<int:pk>/form/', views.DroneOrderForm.as_view(), name='drone-order-form'),
    path('drone_orders/<int:pk>/complete/', views.DroneOrderComplete.as_view(), name='drone-order-complete'),
    path('drone_orders/<int:pk>/delete/', views.DroneOrderDelete.as_view(), name='drone-order-delete'),

    path('drone_items/<int:pk>/update/', views.DroneOrderItemUpdate.as_view(), name='drone-item-update'),
    path('drone_items/<int:pk>/delete/', views.DroneOrderItemDelete.as_view(), name='drone-item-delete'),

    path('drone_users/register/', views.UserRegister.as_view(), name='drone-user-register'),
    path('drone_users/me/', views.UserDetail.as_view(), name='drone-user-me'),
    path('drone_users/login/', views.UserLogin.as_view(), name='drone-user-login'),
    path('drone_users/logout/', views.UserLogout.as_view(), name='drone-user-logout'),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
