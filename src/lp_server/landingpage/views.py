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

import random
import logging
import datetime

from django.conf import settings
from django.core.validators import validate_ipv46_address
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication, BasicAuthentication

from .utils import (
    create_request_history_log,
    get_landing_page,
)
from lp_server.utils import MonitoringPermission

from server.models import OutlineServer
from landingpage.models import (
    RequestSource,
    RequestStatus,
    FailureCause,
    RequestsHistoryAggregate)
from distribution.models import LoadBalancer

logger = logging.getLogger(__name__)


class LandingPageView(View):
    """
    Returns landing page for specified server
    """

    def _retrieve_ip_address(self, request):
        """
        Retrieve IP address from the request
        """
        remote_addr_fwd = None
        beepass_server_ip = None

        ip = request.META.get('REMOTE_ADDR')
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            remote_addr_fwd = request.META['HTTP_X_FORWARDED_FOR'].split(",")[
                0].strip()
            ip = remote_addr_fwd
        if settings.BEEPASS_IP_HEADER_META in request.META:
            beepass_server_ip = request.META[settings.BEEPASS_IP_HEADER_META].split(",")[
                0].strip()
            ip = beepass_server_ip

        try:
            validate_ipv46_address(ip)
        except ValidationError:
            if not beepass_server_ip:
                logger.warning(f'Invalid IP address: {str(ip)}')
            ip = None
            pass

        return ip, remote_addr_fwd, beepass_server_ip

    def _retrieve_source(self, request):
        """
        Retrieve source from the request
        """

        source = RequestSource.BEEPASS
        source_header = settings.IMPRESSION_SOURCE_HEADER
        if source_header and source_header in request.headers:
            source = request.headers.get(source_header)
        return source

    def get(self, request):
        # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        # if x_forwarded_for:
        #     ip = x_forwarded_for.split(',')[0]
        # else:
        #     ip = request.META.get('REMOTE_ADDR')
        #     We don't want the above, we need VPN server's IP address

        source = self._retrieve_source(request)

        if request.path.endswith('/favicon.ico'):
            return HttpResponse(settings.LP_SERVER_NOT_FOUND, status=444)
        ownclient = True
        ownserver = True
        ip, remote_addr_fwd, beepass_server_ip = self._retrieve_ip_address(request)

        if beepass_server_ip is None:
            ownclient = False

        count = 0
        servers = None
        if ip is not None:
            servers = OutlineServer.objects.filter(
                Q(ipv4=ip) | Q(ipv6=ip)).distinct()
            count = servers.count()

        elif beepass_server_ip is not None:
            servers_ids = LoadBalancer.objects.filter(
                host_name=beepass_server_ip).values_list('server').distinct()
            if servers_ids:
                servers = OutlineServer.objects.filter(
                    id__in=servers_ids,
                    active=True)
                count = servers.count()

        if count == 0:
            ownserver = False
            if settings.CHECK_FOR_SERVERS and not beepass_server_ip:      # We are continuing as the user seems to be using a Beepass Client

                # Log invalid request
                create_request_history_log(
                    RequestStatus.INVLAID,
                    ip,
                    remote_addr_fwd,
                    request,
                    source,
                    FailureCause.REQUESTED_SERVERS_NOT_FOUND)

                return HttpResponse(
                    settings.LP_SERVER_NOT_FOUND,
                    status=444)
            else:
                servers = OutlineServer.objects.filter(active=True)
                count = servers.count()

                if count == 0:
                    # Log invalid request
                    create_request_history_log(
                        RequestStatus.INVLAID,
                        ip,
                        remote_addr_fwd,
                        request,
                        source,
                        FailureCause.CHECK_SERVERS_OFF)

                    return HttpResponse(
                        settings.LP_SERVER_NOT_FOUND,
                        status=444)

        server = random.choice(servers)

        with transaction.atomic():
            impression = get_landing_page(server.region)

            if impression is None:
                # Log invalid request
                create_request_history_log(
                    RequestStatus.INVLAID,
                    ip,
                    remote_addr_fwd,
                    request,
                    source,
                    FailureCause.NO_CAMPAIGNS)

                return HttpResponse(
                    settings.LP_SERVER_FOR_REGION_NOT_FOUND,
                    status=444)

            # Log accepted request
            create_request_history_log(
                RequestStatus.ACCEPTED,
                ip,
                remote_addr_fwd,
                request,
                source,
                campaign=impression.campaign,
                ownclient=ownclient,
                ownserver=ownserver)

            # Update Actuals for Impressions
            impression.actual = impression.actual + 1
            impression.save()

        return HttpResponse(impression.campaign.landing_page)


class ImpressionApiView(APIView):
    """
    Impressions per campaign
    """
    authentication_classes = [TokenAuthentication, BasicAuthentication]
    permission_classes = [MonitoringPermission]

    def get(self, request, data_date=None):
        total_impression = RequestsHistoryAggregate.objects.filter(
            status=RequestStatus.ACCEPTED)
        day = datetime.datetime.today()
        if data_date:
            day = datetime.datetime.strptime(data_date, '%Y-%m-%d')
        tz = timezone.get_current_timezone()
        day = timezone.make_aware(day, tz, True)
        next_day = day + datetime.timedelta(days=1)

        source = request.GET.get('source', None)
        filters = {'timestamp__range': (day, next_day)}
        if source:
            filters['source'] = source

        total_impression = total_impression.filter(
            **filters).values(
                'campaign__name').annotate(
                    sum=Sum('count'))
        return JsonResponse(list(total_impression), safe=False)
