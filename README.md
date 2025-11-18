# Drone Battery Predictor

Система прогнозирования скорости разряда аккумулятора дрона для моделирования и расчета времени полета с учетом массы полезной нагрузки, характеристик батареи и погодных условий. Состоит из трёх компонентов: основной веб-сервис на Python/Django, асинхронного сервиса на Go и фронтенд-приложения на React.

## Функциональные возможности
- Расчёт скорости разряда аккумулятора дрона для заданных параметров
- Создание, редактирование и управление заявками на услуги дронов
- Асинхронный прогноз времени полета через отдельный сервис
- Отображение актуальных результатов в веб-приложении

## Используемые технологии
- Backend: Python, Django REST Framework, PostgreSQL, Redis
- Асинхронный сервис: Go
- Frontend: React, Redux Toolkit
- SPA и Tauri приложения
- Развёртывание: GitHub Pages

## Ссылки на проект
- Демо (GitHub Pages): [https://mallartt.github.io/drone-battery-predictor-frontend/](https://mallartt.github.io/drone-battery-predictor-frontend/)  
- Репозиторий Backend: [https://github.com/Mallartt/drone-battery-predictor](https://github.com/Mallartt/drone-battery-predictor)  
- Репозиторий Frontend: [https://github.com/Mallartt/drone-battery-predictor-frontend](https://github.com/Mallartt/drone-battery-predictor-frontend)  
- Репозиторий Асинхронного сервиса: [https://github.com/Mallartt/drone-battery-predictor-async](https://github.com/Mallartt/drone-battery-predictor-async)
