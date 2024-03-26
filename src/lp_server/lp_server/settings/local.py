# Copyright (C) 2024 ASL19 Organization
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .base import *
import os
import sys

BUILD_ENV = 'local'
DEBUG = True
LOG_LEVEL = 'DEBUG'

ALLOWED_HOSTS = ['*']

# Database
DB_USER = os.environ['DATABASE_USER']
DB_PASSWORD = os.environ['DATABASE_PASSWORD']
DB_HOST = os.environ['DATABASE_HOST']
DB_NAME = os.environ['DATABASE_NAME']
DB_PORT = os.environ['DATABASE_PORT']
PROM_DB_USER = os.environ.get('PROM_DATABASE_USER', None)
PROM_DB_PASSWORD = os.environ.get('PROM_DATABASE_PASSWORD', None)
PROM_DB_NAME = os.environ.get('PROM_DATABASE_NAME', None)
PROM_DB_HOST = os.environ.get('PROM_DATABASE_HOST', None)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    },
    'prometheus': {
        'NAME': PROM_DB_NAME,
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': PROM_DB_USER,
        'PASSWORD': PROM_DB_PASSWORD,
        'HOST': PROM_DB_HOST
    }
}

# Media Files
MEDIA_ROOT = os.path.join(BASE_DIR, 'MEDIA')
MEDIA_URL = '/media/'
MEDIAFILES_LOCATION = MEDIA_URL

STATICFILES_LOCATION = STATIC_URL

INTERNAL_IPS = ('127.0.0.1',)

WS_S3_OBJECT_PARAMETERS = {
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'CacheControl': 'max-age=94608000',
}

PROFILE_DELETE_DELAY = 1

REPUTATION_MAP = [0, 2, 20, 50]

# The console EmailBackend will be used for debugging on local and development environments
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REAL_VPN_SERVERS = False