
services_data = [
    {
        'id': 1,
        'name': 'Зависание',
        'description': 'Режим стабильного удержания позиции дрона в воздухе',
        'image': 'http://localhost:9000/images/hovering.jpg',
        'power_multiplier': 0.6
    },
    {
        'id': 2,
        'name': 'Активное маневрирование',
        'description': 'Режим с активным перемещением и сменой высоты',
        'image': 'http://localhost:9000/images/maneuvering.jpg',
        'power_multiplier': 1.0
    },
    {
        'id': 3,
        'name': 'С видеозаписью',
        'description': 'Режим полета с активной видеозаписью в 4K',
        'image': 'http://localhost:9000/images/recording.jpg',
        'power_multiplier': 1.2
    },
    {
        'id': 4,
        'name': 'Доставка груза',
        'description': 'Режим транспортировки небольших посылок или медикаментов',
        'image': 'http://localhost:9000/images/delivery.jpg',
        'power_multiplier': 1.5
    },
    {
        'id': 5,
        'name': 'Тепловизионная съемка',
        'description': 'Режим с использованием тепловизора для поиска объектов и мониторинга',
        'image': 'http://localhost:9000/images/thermal.jpg',
        'power_multiplier': 1.3
    }
]

order_data_template = {
    'id': 1,
    'items': [
        {'service_id': 1},
        {'service_id': 3}
    ],
    'drone_parameters': [
        {'label': 'Масса дрона', 'value': 2},
        {'label': 'Масса груза', 'value': 1},
        {'label': 'Ёмкость аккумулятора mAh', 'value': 5000},
        {'label': 'Напряжение батареи V', 'value': 11.1},
        {'label': 'КПД', 'value': 0.8},
        {'label': 'Остаток заряда (%)', 'value': 85}
    ]
}
