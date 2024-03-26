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

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


def get_s3_url():
    s3_url = None

    if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN'):
        s3_url = 'https://{s3_domain}'.format(
            s3_domain=settings.AWS_S3_CUSTOM_DOMAIN
        )

    return s3_url


class MediaStorage(S3Boto3Storage):
    location = settings.MEDIAFILES_LOCATION
    file_overwrite = False


class StaticStorage(S3Boto3Storage):
    location = settings.STATICFILES_LOCATION
    file_overwrite = False
