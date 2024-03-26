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

from io import StringIO

from django.urls import reverse
from django.conf import settings
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from model_bakery import baker
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from server.models import OutlineServer
from preference.models import Region


class ServerApiTests(APITestCase):

    def setUp(self):
        settings.REAL_VPN_SERVERS = False

        call_command('create_groups', stdout=StringIO())

        # Create a Distributer Admin
        self.distadmin_user = baker.make(get_user_model())
        distadmin_group = Group.objects.filter(name='Distributer Admin')
        self.assertEqual(distadmin_group.count(), 1)
        self.distadmin_user.groups.add(distadmin_group.first())
        self.distadmin_user.save()
        self.distadmin_token = Token.objects.create(user=self.distadmin_user)

        # Create a Distributer
        self.dist_user = baker.make(get_user_model())
        dist_group = Group.objects.filter(name='Distributer')
        self.assertEqual(dist_group.count(), 1)
        self.dist_user.groups.add(dist_group.first())
        self.dist_user.save()
        self.dist_token = Token.objects.create(user=self.dist_user)

        # Create a Server Manager
        self.server_user = baker.make(get_user_model())
        server_group = Group.objects.filter(name='Server Manager')
        self.assertEqual(server_group.count(), 1)
        self.server_user.groups.add(server_group.first())
        self.server_user.save()
        self.server_token = Token.objects.create(user=self.server_user)

        # Badic Distribution i.e. dist_model=0
        self.region_iran = baker.make_recipe('preference.region_iran')
        self.region_mena = baker.make_recipe('preference.region_mena')

        self.location_us = baker.make_recipe('preference.location_us')
        self.location_ger = baker.make_recipe('preference.location_germany')
        self.location_fra = baker.make_recipe('preference.location_france')

        self.server1 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='101.102.103.104',
            name='TG 10A',
            level=0,
            region=[self.region_iran])

    def compareServers(self, serverJson, serverObj):
        self.assertEqual(serverJson['name'], serverObj.name)
        self.assertEqual(serverJson['ipv4'], serverObj.ipv4)
        self.assertEqual(serverJson['ipv6'], serverObj.ipv6)
        self.assertEqual(serverJson['provider'], serverObj.provider)
        self.assertEqual(serverJson['cost'], serverObj.cost)
        self.assertEqual(serverJson['user_src'], serverObj.user_src)
        self.assertEqual(serverJson['reputation'], serverObj.reputation)
        self.assertEqual(serverJson['level'], serverObj.level)
        self.assertEqual(serverJson['dist_model'], serverObj.dist_model)
        self.assertEqual(serverJson['active'], serverObj.active)
        self.assertEqual(serverJson['alert'], serverObj.alert)
        self.assertEqual(serverJson['is_blocked'], serverObj.is_blocked)
        self.assertEqual(serverJson['is_distributing'], serverObj.is_distributing)
        for reg in serverJson['region']:
            regs = Region.objects.filter(id=reg['id'])
            self.assertEqual(regs.count(), 1)
            self.assertEqual(reg['name'], regs[0].name)
        self.assertEqual(serverJson['api_url'], serverObj.api_url)
        self.assertEqual(serverJson['api_cert'], serverObj.api_cert)
        self.assertEqual(serverJson['prometheus_port'], serverObj.prometheus_port)

    def checkCreateOutlineServerApiRequest(self, token=None):
        url = reverse('create-outline-server')

        data = {
            'name': 'CreatedForTest',
            'ipv4': '12.34.56.78',
            'ipv6': '2001:4860:4860::8888',
            'provider': 'TestProvider',
            'cost': 120.52,
            'user_src': 'TG',
            'reputation': 0,
            'api_url': 'https://hsjhgsdjfhgsdfj.com/api',
            'api_cert': 'jkhkjhfkjb',
            'prometheus_port': '900',
            'active': 'True',
            'region': [
                self.region_iran.id,
                self.region_mena.id],
            'dist_model': 0
        }
        response = self.client.put(
            url,
            data=data,
            HTTP_AUTHORIZATION=f'Token {token}')

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        outserver = response.json()
        aftserver = OutlineServer.objects.filter(id=outserver['id'])
        self.assertEqual(aftserver.count(), 1)
        aftserver = aftserver.first()
        self.compareServers(outserver, aftserver)

    def testCreateOutlineServerApiUnpriviledgedRequests(self):
        url = reverse('create-outline-server')

        data = {
            'name': 'CreatedForTest',
            'ipv4': '12.34.56.78',
            'ipv6': '2001:4860:4860::8888',
            'provider': 'TestProvider',
            'cost': 120.52,
            'user_src': 'TG',
            'reputation': 0,
            'api_url': 'https://hsjhgsdjfhgsdfj.com/api',
            'api_cert': 'jkhkjhfkjb',
            'prometheus_port': '900',
            'active': 'True',
            'region': [
                self.region_iran.id,
                self.region_mena.id],
            'dist_model': 0
        }

        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, 401)
        response = self.client.put(url, data=data, HTTP_AUTHORIZATION=f'Token {self.dist_token}')
        self.assertEqual(response.status_code, 403)
        response = self.client.put(url, data=data, HTTP_AUTHORIZATION=f'Token {self.distadmin_token}')
        self.assertEqual(response.status_code, 403)

    def testCreateOutlineServerApiServerManagerRequest(self):
        self.checkCreateOutlineServerApiRequest(self.server_token)

    def checkRetrieveOutlineServerList(self, token):
        url = reverse('list-outline-server')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)
        results = response.json()

        count = 0
        for row in results:
            count += 1
            server = OutlineServer.objects.filter(id=row['id'])
            self.assertEqual(server.count(), 1)
            server = server.first()
            self.compareServers(row, server)

        self.assertEqual(OutlineServer.objects.all().count(), count)

    def testRetrieveOutlineServerListAnonRequest(self):
        url = reverse('list-vpn-users')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveOutlineServerListServerManagerRequest(self):
        self.checkRetrieveOutlineServerList(self.server_token)

    def checkRetrieveOutlineServer(self, token):
        url = reverse('retrieve-outline-server', args=[self.server1.id])
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)
        results = response.json()

        server = OutlineServer.objects.filter(id=results['id'])
        self.assertEqual(server.count(), 1)
        server = server.first()
        self.compareServers(results, server)

    def testRetrieveOutlineServerAnonRequest(self):
        url = reverse('retrieve-outline-server', args=[self.server1.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveOutlineServerDistributerRequest(self):
        self.checkRetrieveOutlineServer(self.server_token)


class ServerTests(TestCase):

    def setUp(self):
        settings.REAL_VPN_SERVERS = False
        self.region_iran = baker.make_recipe('preference.region_iran')
        self.region_mena = baker.make_recipe('preference.region_mena')

        location_us = baker.make_recipe('preference.location_us')
        location_ger = baker.make_recipe('preference.location_germany')
        location_fra = baker.make_recipe('preference.location_france')

        self.basic_server3 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='14.14.14.14',
            name='TG 12',
            level=2,
            region=[self.region_iran])
        baker.make_recipe(
            'server.em_vpn_server',
            ipv4='13.13.13.13',
            name='EM 13',
            level=1,
            region=[self.region_iran])
        baker.make_recipe(
            'server.em_vpn_server',
            ipv4='15.15.15.15',
            name='EM 15',
            level=2,
            region=[self.region_iran])

        locs = [location_us, location_ger, location_fra]
        for i in range(3):
            baker.make_recipe(
                'server.tg_loc_vpn_server',
                ipv4=f'{i+50}.{i+50}.{i+50}.{i+50}',
                name=f'TG {i+50}',
                level=0,
                region=[self.region_iran],
                dist_model=1,
                location=locs[i])
            baker.make_recipe(
                'server.em_loc_vpn_server',
                ipv4=f'{i+20}.{i+20}.{i+20}.{i+20}',
                name=f'EM {i+20}',
                level=0,
                region=[self.region_iran],
                dist_model=1,
                location=locs[i])
            baker.make_recipe(
                'server.tg_loc_vpn_server',
                ipv4=f'{i+30}.{i+30}.{i+30}.{i+30}',
                name=f'TG {i+30}',
                level=1,
                region=[self.region_iran],
                dist_model=1,
                location=locs[i])
            baker.make_recipe(
                'server.em_loc_vpn_server',
                ipv4=f'{i+40}.{i+40}.{i+40}.{i+40}',
                name=f'EM {i+40}',
                level=1,
                region=[self.region_iran],
                dist_model=1,
                location=locs[i])
            baker.make_recipe(
                'server.tg_loc_vpn_server',
                ipv4=f'{i+60}.{i+60}.{i+60}.{i+60}',
                name=f'TG {i+60}',
                level=2,
                region=[self.region_iran],
                dist_model=1,
                location=locs[i])
            baker.make_recipe(
                'server.em_loc_vpn_server',
                ipv4=f'{i+70}.{i+70}.{i+70}.{i+70}',
                name=f'EM {i+70}',
                level=2,
                region=[self.region_iran],
                dist_model=1,
                location=locs[i])

    def testIsServerWorking(self):
        self.basic_server3.is_blocked = False
        self.basic_server3.is_distributing = True
        self.basic_server3.active = True
        self.basic_server3.save()
        self.assertTrue(self.basic_server3.is_working())

        self.basic_server3.is_blocked = True
        self.basic_server3.save()
        self.assertFalse(self.basic_server3.is_working())
        self.basic_server3.is_blocked = False

        self.basic_server3.is_distributing = False
        self.basic_server3.save()
        self.assertFalse(self.basic_server3.is_working())
        self.basic_server3.is_distributing = True

        self.basic_server3.active = False
        self.basic_server3.save()
        self.assertFalse(self.basic_server3.is_working())
        self.basic_server3.active = True

        self.basic_server3.save()
