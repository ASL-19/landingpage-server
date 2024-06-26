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

from django.urls import path, re_path, include
from server import views


urlpatterns = [
    path('outlineservers', views.OutlineServerListView.as_view(), name='list-outline-server'),
    path('outlineserver', views.OutlineServerView.as_view(), name='create-outline-server'),
    re_path(r'outlineserver/(?P<pk>\d+)$', views.OutlineServerView.as_view(), name='retrieve-outline-server'),
]

urlpatterns = [path('server/', include(urlpatterns))]
