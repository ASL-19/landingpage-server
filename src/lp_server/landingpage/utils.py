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
import json
import re
import logging
from hashlib import sha512
from django.utils import timezone
from django.db.models import F
from django.db import transaction, IntegrityError

from django.conf import settings

from landingpage.models import (
    RequestSource, RequestsHistory, RequestsHistoryAggregate,
    FailureCause)
from publisher.models import Impression

logger = logging.getLogger(__name__)


def hashit(value):
    """
    Hash the value and returns digest
    """
    if value is None:
        return ''
    if settings.IPADDRESS_OBFUSCATE == 'HASH':
        return sha512(value.encode('utf-8')).hexdigest()
    else:
        return ''


def clean_headers(headers, changed=False):
    """
    Cleans headers from IP address, specifically
    looks for:
        X-Real-Ip
        X-Forwarded-For
    """
    changed = False
    target_headers = [
        'X-Real-Ip',
        'X-Forwarded-For'
    ]
    ippattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

    headers = dict(headers)

    for header in target_headers:
        value = headers.get(header, None)
        if value is not None:
            if settings.IPADDRESS_OBFUSCATE == 'HASH':
                if re.match(ippattern, value):
                    headers[header] = hashit(value)
                    changed = True
            else:
                if value != '':
                    headers[header] = hashit(value)
                    changed = True
    return json.dumps(headers), changed


def aggregate_request_history_log(status, now_hour, campaign=None):
    """
    Creates a new RequestHistoryAggregate record or updates
    an existing one

    Args:
        status (str): Either accepted or invalid
        now_hour (datetime.datetime): The hour of the record
        campaign (Campaign, optional): The campaign of the selected
            landing page served to the VPN user. Defaults to None.
    """

    try:
        with transaction.atomic():
            # Update the requests history aggregate object
            updated = RequestsHistoryAggregate.objects.filter(
                status=status,
                timestamp=now_hour,
                campaign=campaign).update(count=F('count') + 1)

            if updated == 0:  # if it does not exist
                # Create the requests history aggregate object
                RequestsHistoryAggregate.objects.create(
                    status=status,
                    timestamp=now_hour,
                    campaign=campaign,
                    count=1)  # add 1 to the default count (0)
    except IntegrityError as err:
        logger.error(
            f'Integrity error while creating request history aggregate log: {err}')


def create_request_history_log(
        status, ip_address, ip_address_fwd, request,
        source=RequestSource.BEEPASS, failure_cause=FailureCause.NA,
        campaign=None, ownclient=False, ownserver=False):
    """
    Creates a new RequestHistory object

    Cleans up IP address from database:
    Columns:
        ip_address
        ip_address_fwd
    The headers:
        X-Real-Ip
        X-Forwarded-For
    """

    ip_address = hashit(ip_address)
    ip_address_fwd = hashit(ip_address_fwd)
    headers, _ = clean_headers(request.headers)

    try:
        RequestsHistory.objects.create(
            source=source,
            status=status,
            ip_address=ip_address,
            ip_address_fwd=ip_address_fwd,
            user_agent=request.META.get('HTTP_USER_AGENT'),
            uri=request.build_absolute_uri(),
            method=request.method,
            host=request.get_host(),
            cookies=json.dumps(
                request.COOKIES) if request.COOKIES else None,
            is_secure=request.is_secure(),
            is_ajax=request.is_ajax(),
            path=request.path,
            headers=headers,
            failure_cause=failure_cause,
            ownclient=ownclient,
            ownserver=ownserver,
            campaign=campaign)
    except Exception as exc:
        logger.error(
            'Exception while creating request history log: {}'.format(exc))


def get_landing_page(region=None):
    """
    calculates next landing page to go out
    """

    prob = random.randint(0, 100)
    today = Impression.objects.filter(
        date=timezone.now().date(),
        campaign__approved=True,
        campaign__enabled=True,
        campaign__draft=False,
        campaign__removed=False)

    if region.exists():
        regions = list(region.values_list('id', flat=True))
        today = today.filter(
            campaign__target_regions__in=regions).distinct()

    today = today.order_by('-percentage')

    if today.count() == 0:
        return None

    for imp in today:
        # We skip ahead if the daily plan has been met
        # for a campaign
        if imp.actual >= imp.desired:
            continue
        prob -= imp.percentage
        if prob <= 0:
            return imp

    # Serve internal campaigns in case all daily plans have been met
    internal_imps = today.filter(campaign__internal=True)
    count = internal_imps.count()
    if count > 0:
        random_index = random.randint(0, count - 1)
        return internal_imps[random_index]

    # in case total percentage is not 100 (for each region)
    return today.first()
