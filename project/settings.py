import os
from pathlib import Path
from decouple import config
import firebase_admin
from firebase_admin import credentials
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent

cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

SECRET_KEY = config('DJANGO_KEY')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.appspot.com', 'feadl.io', 'www.feadl.io', 'app.snackski.com', 'www.app.snackski.com']

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "admin",
    "agency",
    "app",
    "funnel",
    "service",
    "website",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

WSGI_APPLICATION = "project.wsgi.application"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

SESSION_COOKIE_AGE = 30 * 60 * 60

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

APPEND_SLASH = False

EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_USE_SSL = config('EMAIL_USE_SSL')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
INTERNAL_RECIPIENTS = config('INTERNAL_RECIPIENTS')

ENVIRONMENT = config('ENVIRONMENT')

AGENCY_USER_PRICE_ID = config('3_DOLLAR_MONTHLY_PRICE_ID')
SERVICE_MONTHLY_PRICE_ID = config('60_DOLLAR_MONTHLY_PRICE_ID')
STANDARD_MONTHLY_PRICE_ID = config('5_DOLLAR_MONTHLY_PRICE_ID')
PREMIUM_MONTHLY_PRICE_ID = config('20_DOLLAR_MONTHLY_PRICE_ID')
AGENCY_MONTHLY_PRICE_ID = config('25_DOLLAR_MONTHLY_PRICE_ID')
STANDARD_ANNUAL_PRICE_ID = config('5_DOLLAR_ANNUAL_PRICE_ID')
PREMIUM_ANNUAL_PRICE_ID = config('20_DOLLAR_ANNUAL_PRICE_ID')
AGENCY_ANNUAL_PRICE_ID = config('20_DOLLAR_ANNUAL_PRICE_ID')


if ENVIRONMENT == 'production':
    print('production')
    # ##------------ DEPLOY -------------##
    # STRIPE_ENDPOINT = config('STRIPE_DEV_ENDPOINT')

    DEBUG = False
    STRIPE_ENDPOINT = config('STRIPE_ENDPOINT')
    STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
    STRIPE_CANCEL_URL = config('STRIPE_CANCEL_URL')
    STRIPE_SUCCESS_URL = config('STRIPE_SUCCESS_URL')
    STRIPE_WEBHOOK_URL = config('STRIPE_WEBHOOK_URL')
    STRIPE_DOMAIN_URL = config('STRIPE_DOMAIN_URL')

    # # DEPLOY SECURITY # #
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    ########################

    REDIRECT_URI = config('REDIRECT_URI')

else:
    print('dev')
    ##------------ DEV -------------##
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    SECURE_PROXY_SSL_HEADER = None
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    
    DEBUG = True
    STRIPE_ENDPOINT = config('STRIPE_LOCAL_ENDPOINT')
    STRIPE_CANCEL_URL = config('STRIPE_DEV_CANCEL_URL')
    STRIPE_SUCCESS_URL = config('STRIPE_DEV_SUCCESS_URL')
    STRIPE_WEBHOOK_URL = config('STRIPE_DEV_WEBHOOK_URL')
    STRIPE_DOMAIN_URL = config('STRIPE_DEV_DOMAIN_URL')
    REDIRECT_URI = config('DEV_REDIRECT_URI')
    STRIPE_SECRET_KEY = config('STRIPE_DEV_SECRET_KEY')
