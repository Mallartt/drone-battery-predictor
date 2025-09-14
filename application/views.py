# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction

from .models import DroneMode, DroneOrder, DroneOrderItem
import math


TRASH = "http://localhost:9000/images/icons8-trash-50.jpg"
dron_img = "http://localhost:9000/images/dron.jpg"
drone_order = "http://localhost:9000/images/zayavka.jpg"

def drone_services(request):
    search_query = request.GET.get("drone_services_search", "")
    services = DroneMode.objects.filter(is_deleted=False)

    if search_query:
        services = services.filter(name__icontains=search_query)

    order = None
    order_items_count = 0
    if request.user.is_authenticated:
        order = DroneOrder.objects.filter(
            creator=request.user, status=DroneOrder.Status.DRAFT
        ).first()
        if order:
            order_items_count = order.items.count()

    return render(
        request,
        "drone_services.html",
        {
            "services": services,
            "order_items_count": order_items_count,
            "order_id": order.id if order else None,
            "search_query": search_query,
            "drone_order": drone_order,
        },
    )


def drone_service(request, id):
    service = get_object_or_404(DroneMode, id=id, is_deleted=False)

    order_items_count = 0
    if request.user.is_authenticated:
        order = DroneOrder.objects.filter(
            creator=request.user, status=DroneOrder.Status.DRAFT
        ).first()
        if order:
            order_items_count = order.items.count()

    return render(
        request,
        "drone_service.html",
        {
            "service": service,
            "order_items_count": order_items_count,
        },
    )


@login_required
def drone_order_detail(request, order_id):
    order = get_object_or_404(DroneOrder, id=order_id, creator=request.user)
    order_items = order.items.select_related("mode")

    drone_fields = [
        ("Вес дрона", "drone_weight"),
        ("Вес груза", "cargo_weight"),
        ("Ёмкость батареи", "battery_capacity"),
        ("Напряжение батареи", "battery_voltage"),
        ("Эффективность", "efficiency"),
        ("Оставшийся заряд батареи", "battery_remaining"),
    ]

    drone_parameters = []
    param_values = {}
    for label, field_name in drone_fields:
        value = getattr(order, field_name, 0) or 0 
        drone_parameters.append((label, value))
        param_values[field_name] = value

    mass_drone = param_values["drone_weight"]
    mass_payload = param_values["cargo_weight"]
    battery_capacity_mAh = param_values["battery_capacity"]
    battery_voltage = param_values["battery_voltage"]
    efficiency = param_values["efficiency"]
    battery_level_pct = param_values["battery_remaining"]

    battery_level = battery_level_pct / 100
    energy_Wh = battery_capacity_mAh * battery_voltage / 1000 * battery_level * efficiency

    for item in order_items:
        mode = item.mode

        multiplier = getattr(mode, "power_multiplier", 1.0) or 1.0
        wind_coeff = getattr(item, "wind_multiplier", 1.0) or 1.0
        rain_coeff = getattr(item, "rain_multiplier", 1.0) or 1.0

        total_mass = mass_drone + mass_payload

        power_W = multiplier * math.pow(total_mass, 1.5) * wind_coeff * rain_coeff

        item.runtime = int((energy_Wh / power_W) * 60) if power_W > 0 else 0

    return render(
        request,
        "drone_battery_order.html",
        {
            "order": order,
            "order_items": order_items,
            "drone_parameters": drone_parameters,
            "order_items_count": order_items.count(),
            "dron_img": dron_img,
            "trash": TRASH,
        },
    )




@login_required
def add_to_drone_order(request, service_id):
    if request.method != "POST":
        return HttpResponse("Метод не разрешён", status=405)

    service = get_object_or_404(DroneMode, id=service_id, is_deleted=False)

    order, created = DroneOrder.objects.get_or_create(
        creator=request.user, status=DroneOrder.Status.DRAFT
    )

    item, created = DroneOrderItem.objects.get_or_create(order=order, mode=service)
    if not created:
        item.save()

    return redirect("drone_services")


@login_required
def delete_drone_order(request, order_id):
    if request.method != "POST":
        return HttpResponse("Метод не разрешён", status=405)

    order = get_object_or_404(DroneOrder, id=order_id, creator=request.user)

    if order.status != DroneOrder.Status.DRAFT:
        return HttpResponse("Можно удалить только черновик", status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE application_droneorder SET status = %s WHERE id = %s",
            [DroneOrder.Status.DELETED, order.id],
        )
        transaction.commit()

    return redirect("drone_services")
