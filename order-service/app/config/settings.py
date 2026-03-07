import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
for env_path in (BASE_DIR / '.env', BASE_DIR.parent / '.env'):
    if env_path.exists():
        environ.Env.read_env(env_path)

SECRET_KEY = env('SECRET_KEY', default='change-me-in-production')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

CART_SERVICE_URL = env('CART_SERVICE_URL', default='http://cart-service:8000')
PAY_SERVICE_URL = env('PAY_SERVICE_URL', default='http://pay-service:8000')
SHIP_SERVICE_URL = env('SHIP_SERVICE_URL', default='http://ship-service:8000')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
