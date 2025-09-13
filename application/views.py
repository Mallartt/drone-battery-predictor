from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction

from .models import DroneMode, DroneOrder, DroneOrderItem


TRASH = "http://localhost:9000/images/icons8-trash-50.jpg"
dron_img = "http://localhost:9000/images/dron.jpg"


def services_list(request):
    search_query = request.GET.get("search", "")
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
        "services.html",
        {
            "services": services,
            "order_items_count": order_items_count,
            "order_id": order.id if order else None,
            "search_query": search_query,
        },
    )


def service_detail(request, id):
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
        "service.html",
        {
            "service": service,
            "order_items_count": order_items_count,
        },
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(DroneOrder, id=order_id, creator=request.user)


    order_items = order.items.select_related("mode")

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
        field = DroneOrder._meta.get_field(field_name)
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


@login_required
def add_to_order(request, service_id):
    if request.method != "POST":
        return HttpResponse("Метод не разрешён", status=405)

    service = get_object_or_404(DroneMode, id=service_id, is_deleted=False)

    order, created = DroneOrder.objects.get_or_create(
        creator=request.user, status=DroneOrder.Status.DRAFT
    )

    item, created = DroneOrderItem.objects.get_or_create(order=order, mode=service)
    if not created:
        item.save()

    return redirect("services_list")


@login_required
def delete_order(request, order_id):
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

    return redirect("services_list")
