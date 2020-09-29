#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import logging.config
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = '4pidf2&gmg@*uw-zl5r)^yq+97ey#c-)%%5di@&5x#5ayv2n_)'
DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'import_export',

    'container',
    'web_admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    # SQLite3
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },

    # PostgreSQL 9.5 trở lên
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #     'NAME': 'tms',
    #     'USER': 'tms',
    #     'PASSWORD': 'Abc12345',
    #     'HOST': 'localhost',
    #     'PORT': '',
    # },
}

AUTH_PASSWORD_VALIDATORS = [
]

USE_I18N = True
USE_L10N = False
LANGUAGE_CODE = 'en-us'

USE_TZ = False
TIME_ZONE = 'UTC'

STATIC_DIR = os.path.join(BASE_DIR, 'static', )

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'web_admin', 'static', ),
)

TEMP_DIR_ROOT = os.path.join(STATIC_DIR, 'tmp', )
TEMP_EMPTY_DIR = os.path.join(STATIC_DIR, 'tmp', 'empty', )

STATIC_URL = '/static/'
STATIC_ROOT = STATIC_DIR

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'web_admin', 'templates', ),
)

LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} p{process:d} thr{thread:d}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': f'{BASE_DIR}/logs/debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'tms': {
            'handlers': ['console', ],
            'level': 'DEBUG',
        },
    },
}
logging.config.dictConfig(LOGGING)
log = logging.getLogger('tms')
