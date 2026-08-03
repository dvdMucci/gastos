from pathlib import Path
from datetime import timedelta
import environ
import os

# Inicializar entorno
env = environ.Env()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Leer archivo .env
environ.Env.read_env(os.path.join(BASE_DIR, '../.env'))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# Se controla desde .env (DJANGO_DEBUG). Por defecto False: si la variable
# falta o está mal escrita, se asume producción.
DEBUG = env.bool('DJANGO_DEBUG', default=False)

# Secreto compartido con n8n para el endpoint de verificación de usuarios.
N8N_API_SECRET = env('N8N_API_SECRET', default='')

ALLOWED_HOSTS = ['gastos.sverina.com.ar', 'localhost', '172.26.0.1', '192.168.208.6', 'django-web-app']


# Application definition

INSTALLED_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'accounts',
    'core',
    'finances',
    'subscriptions',
    'forecasts',
    'income',
    'security',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'axes',

]

AUTH_USER_MODEL = 'accounts.CustomUser'  # Usar el modelo de usuario personalizado

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'core.security_middleware.SecurityMiddleware',  # Bloqueo de IPs y rate limiting
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # Debe ir al final
]

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Debe ir primero
    'django.contrib.auth.backends.ModelBackend',
]

# --- django-axes: límite de intentos de login ---
AXES_FAILURE_LIMIT = 3                     # 3 intentos fallidos
AXES_COOLOFF_TIME = timedelta(minutes=30)  # y queda bloqueado 30 minutos
# Se bloquea la combinación IP + usuario (la lista anidada significa "combinación").
# Bloquear sólo por usuario permitiría que alguien deje afuera a un familiar
# a propósito; bloquear sólo por IP dejaría afuera a toda la casa.
AXES_LOCKOUT_PARAMETERS = [['ip_address', 'username']]
AXES_RESET_ON_SUCCESS = True               # un login exitoso limpia el contador
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_VERBOSE = True

# Detrás de nginx proxy manager la IP real viene en X-Forwarded-For.
AXES_IPWARE_META_PRECEDENCE_ORDER = ('HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR')

# IPs de los proxies de confianza. Sólo si la request viene de una de estas
# se hace caso al header X-Forwarded-For para determinar la IP real.
TRUSTED_PROXY_IPS = env.list('TRUSTED_PROXY_IPS', default=[])

ROOT_URLCONF = 'web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



WSGI_APPLICATION = 'web.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'sql_mode': 'traditional', # Modo SQL para compatibilidad
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
#STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise sirve los estáticos desde gunicorn (comprimidos y cacheados).
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        # Sin manifest: si falta un archivo estático no rompe la página.
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
# OTP Settings
OTP_TOTP_ISSUER = 'Gastos Casita' # Nombre del emisor para la aplicación 2FA
OTP_LOGIN_URL = '/accounts/login/' # URL de login para OTP

# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Ignore connection errors
        }
    }
}

# Cache settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'forecasts'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
CSRF_TRUSTED_ORIGINS = ['https://gastos.sverina.com.ar']  # Añadir dominios de confianza para CSRF

# Configuraciones de Seguridad para Producción
if not DEBUG:
    # Seguridad HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # n8n llama a la API por HTTP dentro de la red de Docker
    # (http://django-web-app:8000/...), donde no hay TLS. Sin estas
    # excepciones el redirect a HTTPS rompería el bot de Telegram.
    SECURE_REDIRECT_EXEMPT = [
        r'^accounts/api/',
        r'^finances/api/',
        r'^income/api/',
        r'^api/security/',
    ]

    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookies seguras
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Headers de seguridad
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Configuración de logging para intentos maliciosos
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '{asctime} {levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'security_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/app/logs/security.log',
                'maxBytes': 5 * 1024 * 1024,  # 5 MB
                'backupCount': 3,
                'formatter': 'simple',
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'loggers': {
            'django.security': {
                'handlers': ['security_file', 'console'],
                'level': 'WARNING',
                'propagate': True,
            },
            # Intentos de login fallidos y bloqueos de django-axes
            'axes': {
                'handlers': ['security_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'core.security_middleware': {
                'handlers': ['security_file', 'console'],
                'level': 'WARNING',
                'propagate': False,
            },
        },
    }