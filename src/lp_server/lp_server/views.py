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
from prometheus_client import multiprocess, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, REGISTRY

from django.utils.encoding import smart_text

from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import renderers
from .utils import MonitoringPermission


class PlainTextRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        return smart_text(data, encoding=self.charset)


class ExportToDjangoView(APIView):
    """
    Exports /metrics as a Django view.
    """
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [MonitoringPermission]
    renderer_classes = [PlainTextRenderer]

    def get(self, request, format=None):
        if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
        else:
            registry = REGISTRY

        metrics_page = generate_latest(registry)

        return Response(
            metrics_page, content_type=CONTENT_TYPE_LATEST
        )
