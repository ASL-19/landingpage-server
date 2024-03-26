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

import os
from django.conf import settings
from django.utils.cache import patch_cache_control


class RevisionMiddleware:
    """
    Added code version to the response
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        revision = '{}b{}-{}'.format(
            str(settings.VERSION_NUM),
            str(settings.BUILD_NUM),
            str(settings.GIT_SHORT_SHA))
        response['X-Source-Revision'] = revision

        return response


class ResponseAndViewManipulationMiddleware:
    """
    Middleware that runs before Django calls view.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.s3_url = None

        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN'):
            self.s3_url = 'https://{s3_domain}'.format(
                s3_domain=settings.AWS_S3_CUSTOM_DOMAIN
            ).encode()

    def __call__(self, request):
        response = self.get_response(request)
        if (response.status_code < 300 or
                request.path.find('^/api/')):
            if (hasattr(request, 'resolver_match') and
                    hasattr(request.resolver_match, 'namespaces') and
                    isinstance(request.resolver_match.namespaces, list) and
                    'api' in request.resolver_match.namespaces):
                patch_cache_control(
                    response,
                    max_age=0,
                    s_maxage=315360000,
                    public=True,
                )

            if (os.environ.get('BUILD_ENV', None) != 'local' and
                    hasattr(settings, 'AWS_CLOUDFRONT_DISTRIBUTION_ID') and
                    isinstance(settings.AWS_CLOUDFRONT_DISTRIBUTION_ID, str) and
                    len(settings.AWS_CLOUDFRONT_DISTRIBUTION_ID) > 0 and
                    self.s3_url):
                response.content = response.content.replace(
                    self.s3_url,
                    b''
                )

        return response


class IntrospectionDisabledException(Exception):
    pass


class DisableIntrospectionMiddleware(object):
    """
    This middleware class hides the introspection.
    """

    def resolve(self, next, root, info, **kwargs):
        if info.field_name.lower() in ['__schema', '__introspection']:
            raise IntrospectionDisabledException
        return next(root, info, **kwargs)
