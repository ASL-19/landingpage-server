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

import json

from django.conf import settings

from rest_framework.test import APITestCase
from model_bakery import baker

from accounts.models import User
from landingpage.models import RequestsHistory, RequestStatus
from freezegun import freeze_time

FREEZE_TIME = '2021-01-01 0:0:0 UTC'


class RequestHistoryTests(APITestCase):
    def setUp(self):
        region_iran = baker.make_recipe('preference.region_iran')

        baker.make_recipe('publisher.great_user')

        organization_group = baker.make_recipe('publisher.organization_group')

        self.great = baker.make_recipe('publisher.great_campaign')
        self.great.target_regions.add(region_iran)
        self.great.save()

        User.objects.get(username='great').groups.add(organization_group)

        self.tg_vpn_server = baker.make_recipe('server.tg_vpn_server')
        self.tg_vpn_server.region.add(region_iran)
        self.tg_vpn_server.save()

    def testRequestHistory(self):
        response = self.client.get(
            '/',
            REMOTE_ADDR=self.tg_vpn_server.ipv4,
            HTTP_USER_AGENT='API Test User Agent')

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        rh = RequestsHistory.objects.last()
        self.assertEqual(rh.status, RequestStatus.ACCEPTED)
        self.assertEqual(rh.ip_address, '')
        self.assertEqual(rh.ip_address_fwd, '')
        self.assertEqual(rh.user_agent, 'API Test User Agent')
        self.assertEqual(rh.method, 'GET')
        self.assertEqual(rh.path, '/')
        self.assertEqual(rh.uri, 'http://testserver/')
        self.assertEqual(rh.host, 'testserver')
        self.assertEqual(rh.campaign, self.great)
        self.assertEqual(rh.ownclient, False)
        self.assertEqual(rh.ownserver, True)

        response = self.client.get(
            '/',
            **{
                'REMOTE_ADDR': self.tg_vpn_server.ipv4,
                'HTTP_USER_AGENT': 'API Test User Agent',
                'HTTP_X_REAL_IP': '140.14.1.123',
                settings.BEEPASS_IP_HEADER_META: self.tg_vpn_server.ipv4,
                'HTTP_X_FORWARDED_FOR': '120.12.1.123,130.13.1.123'
            })

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        rh = RequestsHistory.objects.last()
        self.assertEqual(rh.status, RequestStatus.ACCEPTED)
        self.assertEqual(rh.ip_address, '')
        self.assertEqual(rh.ip_address_fwd, '')
        self.assertEqual(rh.user_agent, 'API Test User Agent')
        self.assertEqual(rh.method, 'GET')
        self.assertEqual(rh.path, '/')
        self.assertEqual(rh.uri, 'http://testserver/')
        self.assertEqual(rh.host, 'testserver')
        self.assertEqual(rh.campaign, self.great)
        self.assertEqual(rh.ownclient, True)
        self.assertEqual(rh.ownserver, True)
        self.assertEqual(json.loads(rh.headers)['X-Forwarded-For'], '')
        self.assertEqual(json.loads(rh.headers)['X-Real-Ip'], '')

        settings.CHECK_FOR_SERVERS = True
        response = self.client.get(
            '/',
            HTTP_USER_AGENT='API Test User Agent')

        self.assertEqual(response.status_code, 444)

        settings.CHECK_FOR_SERVERS = False
        response = self.client.get(
            '/',
            HTTP_USER_AGENT='API Test User Agent')

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        rh = RequestsHistory.objects.last()
        self.assertEqual(rh.status, RequestStatus.ACCEPTED)
        self.assertEqual(rh.ip_address, '')
        self.assertEqual(rh.ip_address_fwd, '')
        self.assertEqual(rh.user_agent, 'API Test User Agent')
        self.assertEqual(rh.method, 'GET')
        self.assertEqual(rh.path, '/')
        self.assertEqual(rh.uri, 'http://testserver/')
        self.assertEqual(rh.host, 'testserver')
        self.assertEqual(rh.campaign, self.great)
        self.assertEqual(rh.ownclient, False)
        self.assertEqual(rh.ownserver, False)

    @freeze_time(FREEZE_TIME)
    def testNoImpressions(self):
        settings.CHECK_FOR_SERVERS = True
        response = self.client.get(
            '/',
            HTTP_USER_AGENT='API Test User Agent')

        self.assertEqual(response.status_code, 444)

        settings.CHECK_FOR_SERVERS = False
        response = self.client.get(
            '/',
            HTTP_USER_AGENT='API Test User Agent')

        self.assertEqual(response.status_code, 444)

    def testBadIpAddress(self):
        response = self.client.get(
            '/',
            **{
                settings.BEEPASS_IP_HEADER_META: '9089.97.76.67',
            })
        self.assertEqual(response.status_code, 200)

    def testNoServers(self):
        self.tg_vpn_server.delete()
        response = self.client.get(
            '/',
            HTTP_USER_AGENT='API Test User Agent')

        self.assertEqual(response.status_code, 444)
