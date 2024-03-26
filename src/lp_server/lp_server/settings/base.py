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

"""
Django settings for lp_server project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import sys
import random
import string
import logging.config
from corsheaders.defaults import default_headers
from datetime import timedelta
from gqlauth.settings_type import GqlAuthSettings

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.field import StrawberryField
from typing import Optional, Annotated


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = int(os.environ.get('DEBUG', default=0))
VERSION_NUM = os.environ.get('VERSION_NUM', 'NA')
BUILD_NUM = os.environ.get('BUILD_NUM', 'NA')
GIT_SHORT_SHA = os.environ.get('GIT_SHORT_SHA', 'NA')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
OUTLINE_TIMEOUT = int(os.environ.get('OUTLINE_TIMEOUT', 30))

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', None)

FRONT_WEB_URL = os.environ.get('FRONT_WEB_URL', None)
BEEPASS_WEB_URL = os.environ.get('BEEPASS_WEB_URL', None)
BEEPASS_IP_HEADER = os.environ.get('BEEPASS_IP_HEADER', None)
if BEEPASS_IP_HEADER:
    BEEPASS_IP_HEADER_META = f'HTTP_{BEEPASS_IP_HEADER.replace("-", "_").upper()}'
IMPRESSION_SOURCE_HEADER = os.environ.get('IMPRESSION_SOURCE_HEADER', None)

# Celery settings
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379')

POD_HOSTNAME = os.environ.get('HOSTNAME', None)
if POD_HOSTNAME is None:
    letters = string.ascii_letters
    POD_HOSTNAME = ''.join(random.choice(letters) for i in range(10))

# Application definition

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_bleach',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'ckeditor',
    'ckeditor_uploader',
    'storages',
    'rangefilter',
    'solo',
    'strawberry.django',
    'strawberry_django',
    'gqlauth',
]

# Local apps
INSTALLED_APPS += [
    'lp_server',
    'preference',
    'publisher',
    'blog',
    'server',
    'landingpage',
    'distribution',
    'reputation',
    'accounts',
    'static_page',
    'notification',
]

# Wagtail apps
INSTALLED_APPS += [
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.contrib.modeladmin',
    'wagtail.contrib.styleguide',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',

    'modelcluster',
    'taggit',
    'wagtailmedia',
]

if 'test' in sys.argv or os.environ.get('BUILD_ENV', None) == 'local':
    RO_DB = 'default'
else:
    RO_DB = 'readonly'

# Needed for user email templates
# and to enable editing the site name and domain
# from the backend
SITE_ID = 1

# Wagtail settings
WAGTAIL_SITE_NAME = 'BeePass uSponsorship Site'
WAGTAIL_EMAIL_MANAGEMENT_ENABLED = False
WAGTAILADMIN_BASE_URL = FRONT_WEB_URL
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'SEARCH_CONFIG': 'english',
    }
}
WAGTAILDOCS_DOCUMENT_FORM_BASE = 'static_page.forms.CustomDocumentForm'

# Wagtailmedia settings
WAGTAILMEDIA = {
    # String, dotted-notation. Defaults to 'wagtailmedia.Media'
    'MEDIA_MODEL': 'wagtailmedia.Media',
    # String, dotted-notation. Defaults to an empty string
    'MEDIA_FORM_BASE': 'static_page.forms.CustomMediaForm',
    'AUDIO_EXTENSIONS': ['aac', 'aiff', 'flac', 'm4a', 'm4b', 'mp3', 'ogg', 'wav'],
    'VIDEO_EXTENSIONS': ['avi', 'h264', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ogv', 'webm'],
}

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'lp_server.middleware.RevisionMiddleware',
    # We don't need SecurityMiddleware, nginx will take care of security headers
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'gqlauth.core.middlewares.django_jwt_middleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # We don't need ClickJacking, nginx will take care of X-Frame header
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lp_server.middleware.ResponseAndViewManipulationMiddleware',
]

ROOT_URLCONF = 'lp_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
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

WSGI_APPLICATION = 'lp_server.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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

def remove_sensitive_data(record):
    if record.status_code == 404:
        for arg in record.args:
            if '/distribution/user/' or '/distribution/outline/' in arg:
                return False
    return True

LOGGING_CONFIG = None
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'filters': {
        'sensitive': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': remove_sensitive_data,
        },
    },
    'loggers': {
        '': {
            'level': LOG_LEVEL,
            'handlers': ['console', ],
        },
        'django.db.backends': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'django.request': {
            'level': LOG_LEVEL,
            'filters': ['sensitive'],
        },
        'django.server': {
            'level': LOG_LEVEL,
            'filters': ['sensitive'],
        },
    },
})


LANGUAGES = (
    ('fa', 'Persian'),
    ('en', 'English'),
)

LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ORIGIN_WHITELIST = [FRONT_WEB_URL] if FRONT_WEB_URL is not None else []

if BEEPASS_WEB_URL:
    CORS_ORIGIN_WHITELIST.extend([BEEPASS_WEB_URL,'https://s3.amazonaws.com'])

CORS_ORIGIN_REGEX_WHITELIST = [
    r"^http:\/\/(10\.)[\d\.]+(:\d+)?$",
    r"^http:\/\/(172\.1[6-9]\.)[\d\.]+(:\d+)?$",
    r"^http:\/\/(172\.2[0-9]\.)[\d\.]+(:\d+)?$",
    r"^http:\/\/(172\.3[0-1]\.)[\d\.]+(:\d+)?$",
    r"^http:\/\/(192\.168\.)[\d\.]+(:\d+)?$",
    r"^http:\/\/localhost(:\d+)?$",
    r"^app:\/\/localhost(:\d+)?$",
]

CORS_ALLOW_HEADERS = list(default_headers)

if BEEPASS_IP_HEADER and IMPRESSION_SOURCE_HEADER:
    CORS_ALLOW_HEADERS = CORS_ALLOW_HEADERS + [
        BEEPASS_IP_HEADER,
        IMPRESSION_SOURCE_HEADER
    ]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'MEDIA')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'static/'

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler', ]

CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_CONFIGS = {
    'default': {
        'basicEntities': False,  # Remove non breaking space chars
        'enterMode': 2,  # Remove automatic <p> tag
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', 'Strike'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source'],
            ['Preview']
        ]
    },
}
AWS_QUERYSTRING_AUTH = False

# Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 15,
    'ORDERING_PARAM': 'ordering',
}

DEFAULT_HIGHLIGHT_PRE_TAGS = '<span class="{}-highlight">'
DEFAULT_HIGHLIGHT_POST_TAGS = '</span>'

PARAGRAPH_HIGHLIGHT_CLASS = 'paragraph'
FOOTNOTE_HIGHLIGHT_CLASS = 'footnote'
SECTION_TITLE_HIGHLIGHT_CLASS = 'section-title'
DOCUMENT_TITLE_HIGHLIGHT_CLASS = 'document-title'
DOCUMENT_TYPE_HIGHLIGHT_CLASS = 'document-type'
CATEGORY_NAME_HIGHLIGHT_CLASS = 'category-name'
TREATY_HIGHLIGHT_CLASS = 'treaty'
ARTICLE_HIGHLIGHT_CLASS = 'article'


# Code constants
MAX_CHARACTER_FOR_TITLE = 200
MAX_HIGHLIGHT_TAG_LEN = 45
MAX_CHARACTER_FOR_EXCERPT = 250

# Swagger
SWAGGER_SETTINGS = {
    'SHOW_REQUEST_HEADERS': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
    ]
}

# Choices
DOCUMENT_PUBLISH_STATUS_DRAFT = 1
DOCUMENT_PUBLISH_STATUS_PUBLISHED = 2
DOCUMENT_PUBLISH_STATUS_CHOICES = (
    (DOCUMENT_PUBLISH_STATUS_DRAFT, 'draft'),
    (DOCUMENT_PUBLISH_STATUS_PUBLISHED, 'published')
)

UTM_URL_TEMPLATE = '{url}?utm_source={source}&utm_medium={medium}&utm_campaign={name}'

LP_SERVER_NOT_FOUND = 'Server does not exist'
LP_SERVER_FOR_REGION_NOT_FOUND = 'Server for the region does not exist'

CHECK_FOR_SERVERS = True

# MODELTRANSLATION
MODELTRANSLATION_LANGUAGES = ('en', 'fa', 'ar')
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

STRAWBERRY_DJANGO = {
    "GENERATE_ENUMS_FROM_CHOICES": True,
    "MAP_AUTO_ID_AS_GLOBAL_ID": True
}

REFRESH_EXPIRATION_COUNTDOWN = 60

# Email settings
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'alias@mail.com')

INVITATION_PATH_ON_EMAIL = 'register'
EMAIL_SUBJECT_INVITATION = 'email/invitation_subject.txt'
EMAIL_TEMPLATE_INVITATION = 'email/invitation_email.html'

username_field = StrawberryField(
    python_name="username", default=None, type_annotation=StrawberryAnnotation(str)
)
password_field = StrawberryField(
    python_name="password", default=None, type_annotation=StrawberryAnnotation(str)
)
first_name_field = StrawberryField(
    python_name="first_name",
    default=None,
    type_annotation=StrawberryAnnotation(Optional[str]),
)
last_name_field = StrawberryField(
    python_name="last_name",
    default=None,
    type_annotation=StrawberryAnnotation(Optional[str]),
)
email_field = StrawberryField(
    python_name="email", default=None, type_annotation=StrawberryAnnotation(str)
)

currency_field = StrawberryField(
    python_name="currency", default=strawberry.UNSET, type_annotation=StrawberryAnnotation(Optional[Annotated['UserCurrency', strawberry.lazy('accounts.schema')]])
)

timezone_field = StrawberryField(
    python_name="time_zone", default=strawberry.UNSET, type_annotation=StrawberryAnnotation(Optional[Annotated['UserTimeZone', strawberry.lazy('accounts.schema')]])
)

GQL_AUTH = GqlAuthSettings(
    LOGIN_REQUIRE_CAPTCHA = False,
    REGISTER_REQUIRE_CAPTCHA = False,
    LOGIN_FIELDS = {username_field},
    ALLOW_LOGIN_NOT_VERIFIED = False,
    ALLOW_PASSWORDLESS_REGISTRATION = False,
    ALLOW_DELETE_ACCOUNT = False,
    SEND_PASSWORD_SET_EMAIL = False,
    EXPIRATION_ACTIVATION_TOKEN = timedelta(days=3),
    EXPIRATION_PASSWORD_RESET_TOKEN = timedelta(minutes=30),
    REGISTER_MUTATION_FIELDS = set([email_field, username_field, first_name_field, last_name_field]),
    UPDATE_MUTATION_FIELDS = set([first_name_field, last_name_field, timezone_field, currency_field]),
    EMAIL_FROM = FROM_EMAIL,
    SEND_ACTIVATION_EMAIL = False,
    PASSWORD_SET_PATH_ON_EMAIL = 'password-set',
    PASSWORD_RESET_PATH_ON_EMAIL = 'password-reset',
    EMAIL_SUBJECT_PASSWORD_RESET = 'email/password_reset_subject.txt',
    EMAIL_TEMPLATE_PASSWORD_RESET = 'email/password_reset_email.html',
    EMAIL_TEMPLATE_VARIABLES = {},
    JWT_PAYLOAD_PK = username_field,
    JWT_LONG_RUNNING_REFRESH_TOKEN = True,
    JWT_EXPIRATION_DELTA = timedelta(minutes=1),
    JWT_REFRESH_EXPIRATION_DELTA = timedelta(hours=1),
)

ADMIN_EMAIL_LIST_CSV = os.environ.get('ADMIN_EMAIL_LIST_CSV', 'alias@mail.com')

EMAIL_SETTINGS = {
    'NEW_USER_NOTIFICATION_PATH_ON_EMAIL': 'admin/accounts/user',
    'EMAIL_SUBJECT_NEW_USER': 'email/new_user_admin_notify_subject.txt',
    'EMAIL_TEMPLATE_NEW_USER': 'email/new_user_admin_notify_email.html',
    'NEW_VERIFICATION_PATH_ON_EMAIL': 'login',
    'EMAIL_SUBJECT_NEW_VERIFICATION': 'email/new_verification_notify_subject.txt',
    'EMAIL_TEMPLATE_NEW_VERIFICATION': 'email/new_verification_notify_email.html',
}

TELEGRAM_HOSTNAME = "https://api.telegram.org"

PURGE_INACTIVE_NOTIFY = 30

IPADDRESS_OBFUSCATE = 'NULL'        # Values are 'NULL' or 'HASH'

REAL_VPN_SERVERS = True

# add, change, delete, view
PREDEFINED_GROUPS = {
    'Distributer Admin': [
        {
            'model': 'online config',
            'permissions': [
                'view'
            ]
        },
        {
            'model': 'issue',
            'permissions': [
                'view'
            ]
        },
        {
            'model': 'account delete reason',
            'permissions': [
                'view'
            ]
        },
        {
            'model': 'vpnuser',
            'permissions': [
                'add',
                'change',
                'view',
                'delete'
            ]
        },
        {
            'model': 'OutlineUser',
            'permissions': [
                'add',
                'change',
                'view'
            ]
        },
        {
            'model': 'location',
            'permissions': [
                'view'
            ],
        },
        {
            'model': 'region',
            'permissions': [
                'view'
            ]
        },
        {
            'model': 'outline server',
            'permissions': [
                'view'
            ]
        }
    ],
    'Distributer': [
        {
            'model': 'issue',
            'permissions': [
                'view'
            ]
        },
        {
            'model': 'account delete reason',
            'permissions': [
                'view'
            ]
        },
        {
            'model': 'vpnuser',
            'permissions': [
                'add',
                'change',
                'view',
                'delete'
            ]
        },
        {
            'model': 'OutlineUser',
            'permissions': [
                'add',
                'change',
                'view'
            ]
        },
        {
            'model': 'location',
            'permissions': [
                'view'
            ],
        },
        {
            'model': 'region',
            'permissions': [
                'view'
            ]
        },
        {
            'model': 'outline server',
            'permissions': [
                'view'
            ]
        }
    ],
    'Server Manager': [
        {
            'model': 'outline server',
            'permissions': [
                'view',
                'add',
                'change'
            ]
        },
    ],
}


# Notification Settings
EXPIRATION_NOTIFICATION_MESSAGE = timedelta(days=5)
# How many days before a new notification message
# become no longer valid for sending (expired)
NOTIFICATION_THRESHOLD_PER_SECOND = 25
NOTIFICATION_MAX_ATTEMPTS_LIMIT = 1
NOTIFICATION_MAX_JOB_BATCH_LIMIT = 17000


# How many days before we delete inactive keys
EXPIRATION_OUTLINE_KEY = timedelta(weeks=1)

IMPRESSION_BILLING_FACTOR = float(os.environ.get('IMPRESSION_BILLING_FACTOR', 1))

# Session setting
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1200
# If this is False, session data will only be saved if modified
SESSION_SAVE_EVERY_REQUEST = True

# Prometheus settings
PROMETHEUS_DEFAULT_PORT = 902