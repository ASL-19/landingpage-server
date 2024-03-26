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

from lp_server.settings.base import *
import os
import sys


BUILD_ENV = 'development'
DEBUG = True
LOG_LEVEL = 'DEBUG'

# Database
DB_USER = os.environ['DATABASE_USER']
DB_PASSWORD = os.environ['DATABASE_PASSWORD']
DB_HOST = os.environ['DATABASE_HOST']
DB_NAME = os.environ['DATABASE_NAME']
DB_PORT = os.environ['DATABASE_PORT']
DB_USER_RO = os.environ['DATABASE_USER_RO']
DB_PASSWORD_RO = os.environ['DATABASE_PASSWORD_RO']
DB_HOST_RO = os.environ['DATABASE_HOST_RO']
DB_NAME_RO = os.environ['DATABASE_NAME_RO']
DB_PORT_RO = os.environ['DATABASE_PORT_RO']
PROM_DB_USER = os.environ.get('PROM_DATABASE_USER', None)
PROM_DB_PASSWORD = os.environ.get('PROM_DATABASE_PASSWORD', None)
PROM_DB_HOST = os.environ.get('PROM_DATABASE_HOST', None)
PROM_DB_NAME = os.environ.get('PROM_DATABASE_NAME', None)
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
AWS_S3_REGION_NAME = os.environ['AWS_S3_REGION_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_DEFAULT_ACL = 'public-read'
DJANGO_ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*')
DJANGO_POD_IP = os.environ.get('POD_IP', None)

ALLOWED_HOSTS = DJANGO_ALLOWED_HOSTS.split(',')
if DJANGO_POD_IP:
    ALLOWED_HOSTS.append(DJANGO_POD_IP)

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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': PROM_DB_NAME,
        'USER': PROM_DB_USER,
        'PASSWORD': PROM_DB_PASSWORD,
        'HOST': PROM_DB_HOST,
    }
}

if 'test' not in sys.argv:
    DATABASES ['readonly'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME_RO,
        'USER': DB_USER_RO,
        'PASSWORD': DB_PASSWORD_RO,
        'HOST': DB_HOST_RO,
        'PORT': DB_PORT_RO,
    }

# Media Files
MEDIA_ROOT = os.path.join(BASE_DIR, 'MEDIA')
MEDIA_URL = '/media/'

DEFAULT_FILE_STORAGE = 'lp_server.media_storage.MediaStorage'
MEDIAFILES_LOCATION = 'media'

INTERNAL_IPS = ('127.0.0.1',)

WS_S3_OBJECT_PARAMETERS = {
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'CacheControl': 'max-age=94608000',
}

# Tell django-storages the domain to use to refer to static files.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# Tell the staticfiles app to use S3Boto3 storage when writing the collected static files (when
# you run `collectstatic`).
STATICFILES_STORAGE = 'lp_server.media_storage.StaticStorage'
STATICFILES_LOCATION = 'static'

PROFILE_DELETE_DELAY = 1

REPUTATION_MAP = [0, 1, 2, 3]

# The console EmailBackend will be used for debugging on local and development environments
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REAL_VPN_SERVERS = False

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
