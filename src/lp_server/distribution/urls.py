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

from django.urls import path, include, re_path
from distribution import views


urlpatterns = [
    re_path(r'user/(?P<username>.+)$', views.VpnuserView.as_view(), name='retrieve-vpn-user'),
    re_path(r'user$', views.VpnuserView.as_view(), name='modify-vpn-user'),
    path('outline', views.OutlineUserView.as_view(), name='modify-outline-user'),
    re_path(r'outline/(?P<user>.+)$', views.OutlineUserView.as_view(), name='retrieve-outline-user'),
    path('users', views.VpnuserList.as_view(), name='list-vpn-users'),
    path('listoutlineusers', views.OutlineUserList.as_view(), name='list-outline-users'),
    path('onlineconfig', views.OnlineConfigView.as_view(), name='modify-online-config'),
    re_path(r'onlineconfig/(?P<user>.+)$', views.OnlineConfigView.as_view(), name='retrieve-online-config'),
    path('listonlineconfigs', views.OnlineConfigList.as_view(), name='list-online-configs'),
    path('issues', views.IssueList.as_view(), name='list-issues'),
    path('deletereasons', views.AccountDeleteReasonList.as_view(), name='list-delete-reasons'),
    path('stats', views.StatisticsDetail.as_view(), name='retrieve-statistics'),
    re_path(r'keyscountserver/$', views.KeysCountServerApiView.as_view()),
    re_path(r'keyscountserver/(?P<server_ip>.+)$', views.KeysCountServerApiView.as_view()),
    re_path(r'keyscountport/(?P<port>.+)$', views.KeysCountPortApiView.as_view()),
    re_path(r'keyscountday/(?P<day>.+)$', views.KeysCountDayApiView.as_view()),
    re_path(r'keyscounthour/(?P<hour>.+)$', views.KeysCountHourApiView.as_view()),
]

urlpatterns = [path('distribution/', include(urlpatterns))]
