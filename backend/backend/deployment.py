import os
from pathlib import Path
from .settings import *

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False
SECRET_KEY = os.environ['MY_SECRET_KEY']

ALLOWED_HOSTS = [os.environ['WEB_HOST'], os.environ['WEB_IP']]
CSRF_TRUSTED_ORIGINS = [f"https://{os.environ['WEB_HOST']}", f"https://{os.environ['WEB_IP']}"]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    f"https://{os.environ['WEB_HOST']}",
    f"https://{os.environ['WEB_IP']}"
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# ADMINS = [("Sagar", "sdreamnewpane@gmail.com")]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ['EMAIL_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_PASSWORD']
DEFAULT_FROM_EMAIL = 'default from email'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
