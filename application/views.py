from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction

from .models import Service, Order, OrderItem


MINIO_BASE_URL = "http://localhost:9000/images"
TRASH = f"{MINIO_BASE_URL}/icons8-trash-50.jpg"
dron_img = "dron.jpg"


def services_list(request):
    search_query = request.GET.get("search", "")
    services = Service.objects.filter(is_active=True)

    if search_query:
        services = services.filter(name__icontains=search_query)

    # Проверка текущей заявки пользователя
    order = None
    order_items_count = 0
    if request.user.is_authenticated:
        order = Order.objects.filter(
            creator=request.user, status=Order.OrderStatus.DRAFT
        ).first()
        if order:
            order_items_count = order.items.count()

    return render(
        request,
        "services.html",
        {
            "services": services,
            "order_items_count": order_items_count,
            "order_id": order.id if order else None,
            "search_query": search_query,
            "minio_base_url": MINIO_BASE_URL,
        },
    )


def service_detail(request, id):
    service = get_object_or_404(Service, id=id, is_active=True)

    order_items_count = 0
    if request.user.is_authenticated:
        order = Order.objects.filter(
            creator=request.user, status=Order.OrderStatus.DRAFT
        ).first()
        if order:
            order_items_count = order.items.count()

    return render(
        request,
        "service.html",
        {
            "service": service,
            "order_items_count": order_items_count,
            "minio_base_url": MINIO_BASE_URL,
        },
    )


@login_required
def order_detail(request):
    # Находим заявку в статусе черновика
    order = Order.objects.filter(
        creator=request.user, status=Order.OrderStatus.DRAFT
    ).first()

    if not order or order.items.count() == 0:
        return HttpResponse("Заявка пуста", status=404)

    # Получаем все услуги внутри заявки
    order_items = order.items.select_related("service")

    # Собираем параметры для отображения
    drone_parameters = []
    for item in order_items:
        drone_parameters.append({
            "service_name": item.service.name,
            "drone_weight": item.drone_weight,
            "cargo_weight": item.cargo_weight,
            "battery_capacity": item.battery_capacity,
            "battery_voltage": item.battery_voltage,
            "efficiency": item.efficiency,
            "battery_remaining": item.battery_remaining,
            "runtime": item.runtime,
            "description": item.description,
        })

    return render(
        request,
        "order.html",
        {
            "order": order,                # сама заявка (Order)
            "order_items": order_items,    # услуги в заявке (OrderItem)
            "drone_parameters": drone_parameters,
            "order_items_count": order_items.count(),
            "dron_img": dron_img,
            "minio_base_url": MINIO_BASE_URL,
            "trash": TRASH,
        },
    )


# --- Добавить услугу в заявку (POST через ORM) ---
@login_required
def add_to_order(request, service_id):
    if request.method != "POST":
        return HttpResponse("Метод не разрешён", status=405)

    service = get_object_or_404(Service, id=service_id, is_active=True)

    # Ищем заявку пользователя в статусе черновика
    order, created = Order.objects.get_or_create(
        creator=request.user, status=Order.OrderStatus.DRAFT
    )

    # Добавляем услугу в заявку
    item, created = OrderItem.objects.get_or_create(order=order, service=service)
    if not created:
        # Если уже есть — можно обновить параметры
        item.save()

    return redirect("order_detail")


# --- Логическое удаление заявки (POST через SQL UPDATE) ---
@login_required
def delete_order(request, order_id):
    if request.method != "POST":
        return HttpResponse("Метод не разрешён", status=405)

    order = get_object_or_404(Order, id=order_id, creator=request.user)

    if order.status != Order.OrderStatus.DRAFT:
        return HttpResponse("Можно удалить только черновик", status=400)

    # SQL UPDATE напрямую
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE application_order SET status = %s WHERE id = %s",
            [Order.OrderStatus.DELETED, order.id],
        )
        transaction.commit()

    return redirect("services_list")
