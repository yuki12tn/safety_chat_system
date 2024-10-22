import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

CHAT_SERVER_HOST = os.getenv('CHAT_SERVER_HOST', '0.0.0.0')
CHAT_SERVER_PORT = int(os.getenv('CHAT_SERVER_PORT', '12345'))


DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',  
    'frontend', 
    'backend', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
    SECURE_CROSS_ORIGIN_OPENER_POLICY = None

ROOT_URLCONF = 'safety_chat_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_TZ = True

STATIC_URL = '/static/'