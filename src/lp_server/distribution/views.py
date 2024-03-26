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

import logging
import datetime

from django.http import Http404, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_csv.renderers import CSVRenderer
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from distribution.utils import get_key_dict, delete_file_from_s3

from lp_server.utils import MonitoringPermission
from lp_server.permissions import RestrictedDjangoModelPermissions
from distribution.models import (
    Vpnuser,
    OutlineUser,
    Issue,
    AccountDeleteReason,
    Statistics,
    BannedReason,
    OnlineConfig)
from server.models import OutlineServer
from distribution.serializers import (
    VpnuserSerializer,
    VpnuserStringSerializer,
    OutlineuserSerializer,
    IssueSerializer,
    StatisticsSerializer,
    AccountDeleteReasonSerializer,
    OnlineConfigSerializer,
    hash_user_id)

logger = logging.getLogger(__name__)


class VpnuserView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to CRUD VPN user
    """
    queryset = Vpnuser.objects.all()
    serializer_class = VpnuserSerializer
    permission_classes = [RestrictedDjangoModelPermissions]

    def get_object(self):
        """
        Override get_object to include Create in the view
        """
        if self.request.method == 'PUT':
            return None
        if self.request.method == 'GET':
            username = self.kwargs.get('username', None)
        else:
            username = self.request.data.get('username', None)
        try:
            user = Vpnuser.objects.get(username=hash_user_id(username))
        except Vpnuser.DoesNotExist:
            raise Http404
        return user

    def perform_destroy(self, instance):
        """
        Override perform_destroy to mark the user to be deleted
        instead of deleting it.
        We also ban the user so they can't use the system.
        """
        if hasattr(settings, 'PROFILE_DELETE_DELAY'):
            days = settings.PROFILE_DELETE_DELAY
        else:
            days = 7
        instance.banned = True
        instance.banned_reason = BannedReason.DELETED
        instance.delete_date = timezone.now() + timezone.timedelta(days=days)
        reason_id = self.request.data.get('reason_id', None)
        try:
            instance.delete_reason = AccountDeleteReason.objects.get(id=reason_id)
        except AccountDeleteReason.DoesNotExist:
            logger.error('Invalid Delete Reason specified!')
            instance.delete_reason = None
        instance.save()

        # Remove OnlineConfig from DB and ssconf files
        try:
            orphan_files = OnlineConfig.objects.filter(outline_user__user=instance)
            for of in orphan_files:
                key = f'{of.file_name}.json'
                try:
                    delete_file_from_s3(
                        settings.S3_SSCONFIG_BUCKET_NAME,
                        key)
                    of.delete()
                except Exception as e:
                    self.stdout.write(self.style.ERROR((f'Unable to get the metadata (bucket={settings.S3_SSCONFIG_BUCKET_NAME}, key={key}) error ({str(e)})')))
        except Exception as e:
            raise e

        # Remove the keys from DB and Servers
        keys = instance.outline_keys.filter(removed=False)
        keys_list = get_key_dict(keys)
        logger.info(f'Deleteing {instance}. Keys to be removed: {keys_list}')
        OutlineuserSerializer.remove_key_from_server(keys_list)
        OutlineuserSerializer.remove_keys_from_db(keys, None)


class VpnuserCSVRenderer(CSVRenderer):
    """
    CSV Renderer for VPN Users
    """
    results_field = 'results'

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
        if data:
            self.header = [
                'username',
                'channel',
                'reputation',
                'delete_date',
                'banned',
                'banned_reason',
                'outline_key',
                'region']
        return super(VpnuserCSVRenderer, self) \
            .render(data, media_type, renderer_context)


class VpnuserList(generics.ListAPIView):
    """
    List of all VPN users in both CSV and JSON
    """
    serializer_class = VpnuserStringSerializer
    permission_classes = [RestrictedDjangoModelPermissions]
    renderer_classes = (VpnuserCSVRenderer, ) + \
        tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get_queryset(self):
        """
        Optionally restricts the returned users list,
        by filtering against a `banned` query parameter in the URL.
        """
        queryset = Vpnuser.objects.all()
        banned = self.request.query_params.get('banned', None)
        if banned in ['True', 'False']:
            queryset = queryset.filter(banned=banned)
        return queryset


class OutlineUserView(generics.RetrieveUpdateAPIView):
    """
    View to Retrieve and Create Outline users
    """
    queryset = OutlineUser.objects.all()
    serializer_class = OutlineuserSerializer
    permission_classes = [RestrictedDjangoModelPermissions]

    def get_object(self):
        """
        Override get_object to include Create in the view
        """
        if self.request.method == 'PUT':
            return None
        elif self.request.method == 'GET':
            user = self.kwargs.get('user', None)
        user = hash_user_id(user)
        ousers = OutlineUser.objects.filter(user__username=user, removed=False)
        if ousers:
            try:
                # TODO: we need to change this for location based servers
                ouser_pk = ousers.last().pk
                ouser = OutlineUser.objects.get(pk=ouser_pk)
            except OutlineUser.DoesNotExist:
                raise Http404
            return ouser
        else:
            raise Http404


class OutlineuserCSVRenderer(CSVRenderer):
    results_field = 'results'

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
        if data:
            self.header = [
                'id',
                'user',
                'server',
                'outline_key',
                'reputation',
                'transfer',
                'user_issue']
        return super(OutlineuserCSVRenderer, self).render(data, media_type, renderer_context)


class OutlineUserList(generics.ListCreateAPIView):
    """
    List of all Outline users in both CSV and JSON
    """

    pagination_class = None
    queryset = OutlineUser.objects.all()
    serializer_class = OutlineuserSerializer
    permission_classes = [RestrictedDjangoModelPermissions]
    renderer_classes = (OutlineuserCSVRenderer, ) + \
        tuple(api_settings.DEFAULT_RENDERER_CLASSES)

    def get_queryset(self):
        """
        Optionally restricts the returned users list,
        by filtering against a `blocked` query parameter in the URL,
        which shows only blocked keys

        if user_issue is None then user hasn't reported the server blocked
        """
        queryset = OutlineUser.objects.filter(removed=False).exclude(user__isnull=True)
        blocked = self.request.query_params.get('blocked', None)
        if blocked is not None:
            if blocked.lower() == 'true':
                blocked = True
            elif blocked.lower() == 'false':
                blocked = False
            else:
                return queryset
            queryset = queryset.filter(user_issue__isnull=not blocked)
        return queryset


class OnlineConfigList(generics.ListAPIView):
    queryset = OnlineConfig.objects.all()
    serializer_class = OnlineConfigSerializer
    permission_classes = [RestrictedDjangoModelPermissions]


class OnlineConfigView(generics.RetrieveUpdateAPIView):
    """
    View to Retrieve and Create OnlineConfigs
    """
    queryset = OnlineConfig.objects.all()
    serializer_class = OnlineConfigSerializer
    permission_classes = [RestrictedDjangoModelPermissions]

    def get_object(self):
        """
        Override get_object to include Create in the view
        """
        if self.request.method == 'PUT':
            return None
        elif self.request.method == 'GET':
            user = self.kwargs.get('user', None)
        try:
            user = Vpnuser.objects.get(username=hash_user_id(user))
        except Vpnuser.DoesNotExist:
            raise Http404
        ousers = OutlineUser.objects.filter(user__username=user, removed=False)
        if ousers:
            try:
                # TODO: we need to change this for location based servers
                ouser_pk = ousers.last().pk
                ouser = OutlineUser.objects.get(pk=ouser_pk)
            except OutlineUser.DoesNotExist:
                raise Http404
        else:
            raise Http404
        try:
            online_config = OnlineConfig.objects.get(outline_user=ouser)
        except OnlineConfig.DoesNotExist:
            raise Http404
        return online_config


class IssueList(generics.ListAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [RestrictedDjangoModelPermissions]


class AccountDeleteReasonList(generics.ListAPIView):
    queryset = AccountDeleteReason.objects.all()
    serializer_class = AccountDeleteReasonSerializer
    permission_classes = [RestrictedDjangoModelPermissions]


class StatisticsDetail(generics.RetrieveAPIView):
    """
    View to Retrieve Statistics
    """

    def get(self, request, *args, **kwargs):
        """
        Override get to retrieve pk=1
        """

        resp_data = StatisticsSerializer(Statistics.objects.get(pk=1)).data
        return Response(resp_data)


class KeysCountServerApiView(APIView):
    """
    Total keys per central server
    """
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [MonitoringPermission]

    def get(self, request, server_ip=None):
        if server_ip:
            # Count keys on one server
            try:
                server = OutlineServer.objects.get(Q(ipv4=server_ip) | Q(ipv6=server_ip))
            except Exception:
                return JsonResponse(-1, safe=False)

            total_keys_count = OutlineUser.objects.filter(
                server=server,
                active=True,
                exists_on_server=True).count()
            return JsonResponse(total_keys_count, safe=False)
        else:
            # Count keys on all servers
            total_keys_count = OutlineUser.objects.filter(
                active=True,
                exists_on_server=True).count()

        return JsonResponse(total_keys_count, safe=False)


class KeysCountPortApiView(APIView):
    """
    Total keys per prefix port
    """
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [MonitoringPermission]

    def get(self, request, port):

        def prefix_port(outline_user):
            ss_link = outline_user.outline_key
            ss_link = ss_link[5:].split("/")[0]
            ss_link = ss_link.split("@")
            ss_ip_port = ss_link[1].split(":")
            server_port = ss_ip_port[1] if '?' not in ss_ip_port[1] else ss_ip_port[1].split('?')[0]
            return server_port

        if port:
            keys = []
            for user in OutlineUser.objects.filter(
                    active=True,
                    exists_on_server=True):
                try:
                    if prefix_port(user) == port:
                        keys.append(user)
                except Exception:
                    continue

            return JsonResponse(len(keys), safe=False)


class KeysCountDayApiView(APIView):
    """
    Total created keys per day
    """
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [MonitoringPermission]

    def get(self, request, day):

        if day:
            start_date = datetime.datetime.strptime(day, '%Y-%m-%d')
            end_date = start_date + datetime.timedelta(days=1)
            keys_count = OutlineUser.objects.filter(
                active=True,
                exists_on_server=True,
                created_date__range=(start_date, end_date)).count()

            return JsonResponse(keys_count, safe=False)


class KeysCountHourApiView(APIView):
    """
    Total created keys per hour
    """
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [MonitoringPermission]

    def get(self, request, hour):

        if hour:
            start_date = datetime.datetime.strptime(hour, '%Y-%m-%d-%H:%M')
            end_date = start_date + datetime.timedelta(hours=1)
            keys_count = OutlineUser.objects.filter(
                active=True,
                exists_on_server=True,
                created_date__range=(start_date, end_date)).count()

            return JsonResponse(keys_count, safe=False)
