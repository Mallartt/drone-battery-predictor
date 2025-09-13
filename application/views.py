# views.py
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
import math
import requests
from .static_data import services_data, order_data_template

default_img = "http://localhost:9000/images/img.jpg"
TRASH = "http://localhost:9000/images/icons8-trash-50.jpg"
dron_img = "http://localhost:9000/images/dron.jpg"
drone_order = "http://localhost:9000/images/zayavka.jpg"

SERVICE_FIELDS = [
    "id", "name", "description", "image", "power_multiplier", "wind_coeff", "rain_coeff"
]

labels = [
    "Масса дрона",
    "Масса груза",
    "Ёмкость аккумулятора mAh",
    "Напряжение батареи V",
    "КПД",
    "Остаток заряда (%)",
]

def as_dict(service_list):
    """Преобразует список значений в словарь с ключами"""
    return dict(zip(SERVICE_FIELDS, service_list))

def ensure_image(data: dict, key: str = "image"):
    filename = data.get(key)
    if not filename:
        data[key] = default_img
        return data
    try:
        response = requests.head(filename, timeout=2)
        if response.status_code != 200:
            data[key] = default_img
    except requests.RequestException:
        data[key] = default_img
    return data

def drone_services(request):
    search_query = request.GET.get('drone_services_search', '').lower()
    services = [as_dict(s) for s in services_data]

    if search_query:
        filtered_services = [s for s in services if search_query in s["name"].lower()]
    else:
        filtered_services = services

    filtered_services = [ensure_image(s) for s in filtered_services]

    order_items_raw = order_data_template[0]

    return render(request, 'drone_services.html', {
        'services': filtered_services,
        'order_items_count': len(order_items_raw),
        'search_query': search_query,
        'order_id': 1,
        'drone_order': drone_order
    })



def drone_service(request, id):
    services = [as_dict(s) for s in services_data]
    service = next((s for s in services if s['id'] == id), None)
    if not service:
        return HttpResponse("Услуга не найдена")
    service = ensure_image(service)
    return render(request, 'drone_service.html', {
        'service': service,
        'order_items_count': len(order_data_template),
    })

def drone_battery_order(request, order_id):
    order_items_raw = order_data_template[0]
    drone_parameters = order_data_template[1]

    if not any(row[0] == order_id for row in order_items_raw):
        return HttpResponseNotFound("Заявка не найдена")

    services = [as_dict(s) for s in services_data]

    order_items = []
    for row in order_items_raw:
        _, service_id = row
        service = next((s for s in services if s['id'] == service_id), None)
        if service:
            service = ensure_image(service)
            order_items.append({
                'service': service,
                'description': service.get('description', '')
            })

    mass_drone, mass_payload, battery_capacity_mAh, battery_voltage, efficiency, battery_level_pct = drone_parameters
    battery_level = battery_level_pct / 100
    energy_Wh = battery_capacity_mAh * battery_voltage / 1000 * battery_level * efficiency

    for it in order_items:
        service = it['service']
        multiplier = service.get('power_multiplier', 1.0)
        wind_coeff = service.get('wind_coeff', 1.0)
        rain_coeff = service.get('rain_coeff', 1.0)

        total_mass = mass_drone + mass_payload
        power_W = multiplier * math.pow(total_mass, 1.5) * wind_coeff * rain_coeff

        it['runtime'] = int((energy_Wh / power_W) * 60) if power_W > 0 else 0

    return render(request, 'drone_battery_order.html', {
        'order_items': order_items,
        'drone_parameters': list(zip(labels, drone_parameters)),
        'order_items_count': len(order_items),
        'dron_img': dron_img,
        'trash': TRASH
    })
