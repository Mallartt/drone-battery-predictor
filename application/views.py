from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction

from .models import Service, Order, OrderItem


TRASH = "http://localhost:9000/images/icons8-trash-50.jpg"
dron_img = "http://localhost:9000/images/dron.jpg"


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
        },
    )


@login_required
def order_detail(request, order_id):
    # Находим заявку по ID и пользователю
    order = get_object_or_404(Order, id=order_id, creator=request.user)

    if order.status != Order.OrderStatus.DRAFT or order.items.count() == 0:
        return HttpResponse("Заявка пуста", status=404)

    order_items = order.items.select_related("service")

    # Собираем параметры дрона через verbose_name
    drone_parameters = []
    drone_fields = [
        "drone_weight",
        "cargo_weight",
        "battery_capacity",
        "battery_voltage",
        "efficiency",
        "battery_remaining",
    ]

    for field_name in drone_fields:
        field = OrderItem._meta.get_field(field_name)
        value = getattr(order, field_name, None)
        drone_parameters.append({
            "label": field.verbose_name,
            "value": value if value is not None else 0
        })

    return render(
        request,
        "order.html",
        {
            "order": order,
            "order_items": order_items,
            "drone_parameters": drone_parameters,
            "order_items_count": order_items.count(),
            "dron_img": dron_img,
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

    return redirect("services_list")


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
