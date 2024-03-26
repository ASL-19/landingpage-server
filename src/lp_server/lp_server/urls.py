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
from django.contrib import admin
from django.urls import re_path, include
from django.views.decorators.csrf import csrf_exempt

from strawberry.django.views import GraphQLView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls

from lp_server.views import ExportToDjangoView
from lp_server.schema import schema
from landingpage.views import ImpressionApiView
from landingpage.views import LandingPageView

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^cms/', include(wagtailadmin_urls)),
    re_path(r'^documents/', include(wagtaildocs_urls)),
    re_path(r'^pages/', include(wagtail_urls)),
    re_path(r'^graphql/', csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=settings.DEBUG))),
    re_path(r'^accounts/', include('django.contrib.auth.urls')),
    re_path(r'^api-auth/', include(('rest_framework.urls', 'rest_framework'), namespace='rest_framework')),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
    re_path(r'^api/v1/metrics', ExportToDjangoView.as_view(), name="lpserver-metrics"),
    re_path(r'^api/v1/impressions/(?P<data_date>.+)$', ImpressionApiView.as_view()),
    re_path(r'^api/v1/impressions/$', ImpressionApiView.as_view()),
    re_path(r'^api/v1/', include('distribution.urls')),
    re_path(r'^api/v1/', include('server.urls')),
    re_path(r'^$', LandingPageView.as_view()),
]

if settings.BUILD_ENV != 'production' and settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]

if settings.BUILD_ENV == 'local':
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
