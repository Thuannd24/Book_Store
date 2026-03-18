import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
for env_path in (BASE_DIR / '.env', BASE_DIR.parent / '.env'):
    if env_path.exists():
        environ.Env.read_env(env_path)

SECRET_KEY = env('SECRET_KEY', default='change-me')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'gateway',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'gateway.middleware.RequestLoggingMiddleware',
    'gateway.middleware.RateLimitMiddleware',
    'gateway.middleware.JWTAuthMiddleware',
    'django.middleware.common.CommonMiddleware',
]

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
])
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Downstream service URLs
CUSTOMER_SERVICE_URL = env('CUSTOMER_SERVICE_URL', default='http://customer-service:8000')
BOOK_SERVICE_URL = env('BOOK_SERVICE_URL', default='http://book-service:8000')
CART_SERVICE_URL = env('CART_SERVICE_URL', default='http://cart-service:8000')
ORDER_SERVICE_URL = env('ORDER_SERVICE_URL', default='http://order-service:8000')
REVIEW_SERVICE_URL = env('REVIEW_SERVICE_URL', default='http://comment-rate-service:8000')
RECOMMENDER_SERVICE_URL = env('RECOMMENDER_SERVICE_URL', default='http://recommender-ai-service:8000')
CATALOG_SERVICE_URL = env('CATALOG_SERVICE_URL', default='http://catalog-service:8000')
STAFF_SERVICE_URL = env('STAFF_SERVICE_URL', default='http://staff-service:8000')
MANAGER_SERVICE_URL = env('MANAGER_SERVICE_URL', default='http://manager-service:8000')
AUTH_SERVICE_URL = env('AUTH_SERVICE_URL', default='http://auth-service:8000')

# Feature flags
JWT_AUTH_ENABLED = env.bool('JWT_AUTH_ENABLED', default=False)
RATE_LIMIT_ENABLED = env.bool('RATE_LIMIT_ENABLED', default=False)

# Cache (Redis or LocMem fallback)
REDIS_URL = env('REDIS_URL', default='')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
