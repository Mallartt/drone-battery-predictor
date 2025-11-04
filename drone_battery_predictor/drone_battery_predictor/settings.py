# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure--k(*szu@2d6)96c=9&qn%-__yvc(y9(o*uz0i0(d6fczvtnu!^'

DEBUG = True
ALLOWED_HOSTS = ['*']

# --- Apps ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'drone_stocks',
    "corsheaders",
    "django_extensions",
    
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = 'drone_battery_predictor.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'drone_battery_predictor.wsgi.application'

# --- Database ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'RIP',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
STATIC_URL = "/static/"
#STATICFILES_DIRS = [BASE_DIR / "static"]       # папка со статикой внутри проекта
STATIC_ROOT = BASE_DIR / "staticfiles"         # куда собирать collectstatic на проде

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# --- DRF ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # ✅ Сессии/куки
        'rest_framework.authentication.TokenAuthentication',    # JWT/токен
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# --- Swagger ---
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': True,
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Добавьте префикс: Token <your_token>'
        }
    },
    'LOGIN_URL': '/drone_users/login/',
    'LOGOUT_URL': '/drone_users/logout/',
    'DEFAULT_INFO': 'drone_battery_predictor.urls.schema_view',
}

# --- Redis sessions ---
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://:password@127.0.0.1:6379/1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# --- MinIO / S3 ---
AWS_STORAGE_BUCKET_NAME = 'images'
AWS_ACCESS_KEY_ID = 'root'
AWS_SECRET_ACCESS_KEY = 'rootroot'
AWS_S3_ENDPOINT_URL = "localhost:9000"  # для boto3
AWS_S3_PUBLIC_URL = "http://localhost:9000"  # для браузера

MINIO_USE_SSL = False

# settings.py (добавить)
ASYNC_SERVICE_URL = "http://127.0.0.1:8080/process"   # URL Go-сервиса
ASYNC_SECRET_KEY = "ABC123XYZ"  # тот же ключ что и в views.py (у тебя уже есть ASYNC_SECRET_KEY в views.py, согласуй)
