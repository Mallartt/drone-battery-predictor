from django.shortcuts import render
from django.http import HttpResponse
import math
from .static_data import services_data, order_data_template
import requests
from django.http import HttpResponseNotFound

default_img = "http://localhost:9000/images/img.jpg"
TRASH = f"http://localhost:9000/images/icons8-trash-50.jpg"
dron_img = 'http://localhost:9000/images/dron.jpg'



def ensure_image(data: dict, key: str = "image"):
    filename = data.get(key)
    if not filename:
        data[key] = default_img
        return data
    
    url = f"{filename}"
    try:
        response = requests.head(url, timeout=2)
        if response.status_code != 200:
            data[key] = default_img
    except requests.RequestException:
        data[key] = default_img
    return data


def services_list(request):
    search_query = request.GET.get('search', '')
    filtered_services = [s.copy() for s in services_data if search_query.lower() in s['name'].lower()] if search_query else [s.copy() for s in services_data]

    filtered_services = [ensure_image(s) for s in filtered_services]

    return render(request, 'services.html', {
    'services': filtered_services,
    'order_items_count': len(order_data_template['items']),
    'search_query': search_query,
    'order_id': order_data_template.get('id'),
})


def service_detail(request, id):
    service = next((s.copy() for s in services_data if s['id'] == id), None)
    if not service:
        return HttpResponse("Услуга не найдена")

    service = ensure_image(service)

    return render(request, 'service.html', {
        'service': service,
        'order_items_count': len(order_data_template['items']),
    })


def order_detail(request, order_id):
    if order_id != order_data_template['id']:
        return HttpResponseNotFound("Заявка не найдена")

    order_data = order_data_template.copy()
    
    order_items = []
    for item in order_data['items']:
        service = next((s.copy() for s in services_data if s['id'] == item['service_id']), None)
        if service:
            service = ensure_image(service)
            order_items.append({
                'service': service,
                'description': service.get('description', '')  
            })

    drone_parameters = order_data['drone_parameters']

    mass_drone = drone_parameters[0]['value']
    mass_payload = drone_parameters[1]['value'] 
    battery_capacity_mAh = drone_parameters[2]['value']
    battery_voltage = drone_parameters[3]['value']
    efficiency = drone_parameters[4]['value']
    battery_level = drone_parameters[5]['value'] / 100

    energy_Wh = battery_capacity_mAh * battery_voltage / 1000 * battery_level * efficiency

    for it in order_items:
        service = it['service']
        multiplier = service.get('power_multiplier', 1.0)

        total_mass = mass_drone + mass_payload
        power_W = multiplier * math.pow(total_mass, 1.5)
        
        if power_W > 0:
            runtime_minutes = (energy_Wh / power_W) * 60
            it['runtime'] = int(runtime_minutes)
        else:
            it['runtime'] = 0

    return render(request, 'order.html', {
        'order': order_data,
        'order_items': order_items,
        'drone_parameters': drone_parameters,
        'order_items_count': len(order_items),
        'dron_img': dron_img,
        'trash': TRASH
    })
