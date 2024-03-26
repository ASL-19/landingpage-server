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

import csv
import json
from datetime import datetime
from io import StringIO

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

import dateutil
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from model_bakery import baker
from freezegun import freeze_time
from freezegun.api import datetime_to_fakedatetime

from distribution.utils import str2bool, get_key_dict
from distribution.models import (
    Vpnuser, OutlineUser,
    Issue, AccountDeleteReason,
    BannedReason)
from distribution.serializers import OutlineuserSerializer


FREEZE_TIME = '2021-01-01 0:0:0 UTC'


class VPNUserApiTests(APITestCase):

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

        # Create a Distributer Admin
        self.dist_user = baker.make(get_user_model())
        dist_group = Group.objects.filter(name='Distributer')
        self.assertEqual(dist_group.count(), 1)
        self.dist_user.groups.add(dist_group.first())
        self.dist_user.save()
        self.dist_token = Token.objects.create(user=self.dist_user)

        # Badic Distribution i.e. dist_model=0
        self.region_iran = baker.make_recipe('preference.region_iran')
        self.region_mena = baker.make_recipe('preference.region_mena')

        location_us = baker.make_recipe('preference.location_us')
        location_ger = baker.make_recipe('preference.location_germany')
        location_fra = baker.make_recipe('preference.location_france')

        self.vuser1 = baker.make_recipe(
            'distribution.vpnuser',
            username='vuser1',
            channel='TG',
            region=[self.region_iran])
        self.vuser2 = baker.make_recipe(
            'distribution.vpnuser',
            username='vuser2@example.com',
            channel='EM',
            region=[self.region_iran])
        self.vuser3 = baker.make_recipe(
            'distribution.vpnuser',
            channel='TG')

        basic_server1 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='10.10.10.10',
            name='TG 10',
            level=0,
            region=[self.region_iran],
            type='legacy')
        basic_server2 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='11.11.11.11',
            name='TG 11',
            level=1,
            region=[self.region_iran],
            type='legacy')
        self.basic_server3 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='14.14.14.14',
            name='TG 12',
            level=2,
            region=[self.region_iran],
            type='legacy')
        self.basic_server3 = baker.make_recipe(
            'server.em_vpn_server',
            ipv4='12.12.12.12',
            name='EM 12',
            level=0,
            region=[self.region_iran],
            type='legacy')
        baker.make_recipe(
            'server.em_vpn_server',
            ipv4='13.13.13.13',
            name='EM 13',
            level=1,
            region=[self.region_iran],
            type='legacy')
        baker.make_recipe(
            'server.em_vpn_server',
            ipv4='15.15.15.15',
            name='EM 15',
            level=2,
            region=[self.region_iran],
            type='legacy')

        self.ouser1 = baker.make_recipe(
            'distribution.outlineuser',
            user=self.vuser1,
            server=basic_server1)
        self.ouser2 = baker.make_recipe(
            'distribution.outlineuser',
            user=self.vuser2,
            server=basic_server2)
        self.ouser3 = baker.make_recipe(
            'distribution.outlineuser',
            user=self.vuser3,
            server=self.basic_server3)

        # Location Based Distribution i.e. dist_model=1
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

    def checkRetrieveVpnuserApiRequest(self, user, token=None):
        url = reverse('retrieve-vpn-user', args=[user.username])

        if token:
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
        else:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        outuser = response.json()
        self.assertEqual(outuser['username'], user.username)
        self.assertEqual(outuser['channel'], user.channel)
        self.assertEqual(outuser['reputation'], user.reputation)
        self.assertEqual(outuser['delete_date'], user.delete_date)
        self.assertEqual(outuser['banned'], user.banned)
        self.assertEqual(outuser['banned_reason'], user.banned_reason)
        self.assertEqual(outuser['userchat'], user.userchat)
        self.assertEqual(
            outuser['region'],
            list(user.region.all().values_list('id', flat=True)))
        self.assertIsNotNone(outuser['outline_key'])
        self.assertEqual(len(outuser['outline_key']), 1)
        self.assertEqual(
            outuser['outline_key'][0]['outline_key_id'],
            user.get_keys()[0].outline_key_id)
        self.assertEqual(
            outuser['outline_key'][0]['server'],
            user.get_keys()[0].server.id)
        self.assertEqual(
            outuser['outline_key'][0]['outline_key'],
            user.get_keys()[0].outline_key)

    def testRetrieveVpnuserApiAnonRequest(self):
        url = reverse('retrieve-vpn-user', args=[self.vuser1.username])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveVpnuserApiDistributorRequest(self):
        self.checkRetrieveVpnuserApiRequest(self.vuser1, self.dist_token)
        self.checkRetrieveVpnuserApiRequest(self.vuser2, self.dist_token)

    def testRetrieveVpnuserApiDistributorAdminRequest(self):
        self.checkRetrieveVpnuserApiRequest(self.vuser1, self.distadmin_token)
        self.checkRetrieveVpnuserApiRequest(self.vuser2, self.distadmin_token)

    def testDeleteVpnuserApiAnonRequest(self):
        url = reverse('retrieve-vpn-user', args=[self.vuser1.username])

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def testDeleteVpnuserApiDistributerRequest(self):
        self.checkDeleteVpnuserApiRequest(self.vuser2, self.distadmin_token)

    @freeze_time(FREEZE_TIME)
    def checkDeleteVpnuserApiRequest(self, user, token):
        url = reverse('modify-vpn-user')

        prevuser = Vpnuser.objects.filter(username=user.username)
        self.assertEqual(prevuser.count(), 1)
        self.assertFalse(prevuser.first().banned)
        self.assertIsNone(prevuser.first().delete_date)

        days = getattr(settings, 'PROFILE_DELETE_DELAY', 7)
        frozen_datetime = (
            datetime(2021, 1, 1, tzinfo=dateutil.tz.UTC) +
            dateutil.relativedelta.relativedelta(days=days))
        data = {
            'username': user.username,
            'reason': 'Testing...'
        }
        response = self.client.delete(
            url,
            data=data,
            HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')

        aftuser = Vpnuser.objects.get(username=user.username)
        self.assertTrue(aftuser.banned)
        self.assertEqual(aftuser.banned_reason, BannedReason.DELETED)
        self.assertEqual(
            datetime_to_fakedatetime(aftuser.delete_date),
            frozen_datetime)

    def testDeleteVpnuserApiAdminDistributorRequest(self):
        self.checkDeleteVpnuserApiRequest(self.vuser1, self.distadmin_token)

    def testModifyVpnuserApiAnonRequest(self):
        url = reverse('modify-vpn-user')

        data = {
            'username': self.vuser1.username,
            'channel': 'EM',
            'banned': True,
            'region': [self.region_iran.id, self.region_mena.id],
            'reputation': 1
        }

        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 401)

    @freeze_time(FREEZE_TIME)
    def checkModifyVpnuserApiRequest(self, user, token):
        url = reverse('modify-vpn-user')

        prevuser = Vpnuser.objects.filter(username=user.username)
        self.assertEqual(prevuser.count(), 1)

        newchannel = 'EM' if user.channel == 'TG' else 'TG'
        data = {
            'username': user.username,
            'channel': newchannel,
            'banned': True,
            'region': [self.region_iran.id, self.region_mena.id],
            'reputation': 1
        }
        response = self.client.patch(
            url,
            data=data,
            HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        aftuser = Vpnuser.objects.get(username=user.username)
        self.assertEqual(aftuser.channel, newchannel)
        self.assertTrue(aftuser.banned)
        self.assertEqual(aftuser.banned_reason, BannedReason.API_UPDATE)
        self.assertEqual(
            list(aftuser.region.all().values_list('id', flat=True)),
            [self.region_iran.id, self.region_mena.id])
        self.assertEqual(aftuser.reputation, 1)

    def testModifyVpnuserApiAdminDistributorRequest(self):
        self.checkModifyVpnuserApiRequest(self.vuser1, self.distadmin_token)
        self.checkModifyVpnuserApiRequest(self.vuser2, self.distadmin_token)

    def testModifyVpnuserApiDistributorRequest(self):
        self.checkModifyVpnuserApiRequest(self.vuser1, self.dist_token)
        self.checkModifyVpnuserApiRequest(self.vuser2, self.dist_token)

    def testAddVpnuserApiAnonRequest(self):
        url = reverse('modify-vpn-user')

        data = {
            'username': 'vuser1-new',
            'channel': 'EM',
            'banned': False,
            'region': [self.region_iran.id],
            'reputation': 1
        }

        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 401)

    @freeze_time(FREEZE_TIME)
    def checkAddVpnuserApiRequest(self, username, channel, token):
        url = reverse('modify-vpn-user')

        prevuser = Vpnuser.objects.filter(username=username)
        self.assertEqual(prevuser.count(), 0)

        data = {
            'username': username,
            'channel': channel,
            'banned': False,
            'region': [self.region_iran.id, self.region_mena.id],
            'reputation': 0
        }
        response = self.client.put(
            url,
            data=data,
            HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        aftuser = Vpnuser.objects.get(username=username)
        self.assertEqual(aftuser.channel, channel)
        self.assertFalse(aftuser.banned)
        self.assertEqual(aftuser.banned_reason, BannedReason.NA)
        self.assertEqual(
            list(aftuser.region.all().values_list('id', flat=True)),
            [self.region_iran.id, self.region_mena.id])
        self.assertEqual(aftuser.reputation, 0)

    def testAddVpnuserApiAdminDistributorRequest(self):
        self.checkAddVpnuserApiRequest('vuser2-new', 'TG', self.distadmin_token)
        self.checkAddVpnuserApiRequest('vuser2-new@example.com', 'EM', self.distadmin_token)

    def testAddVpnuserApiDistributorRequest(self):
        self.checkAddVpnuserApiRequest('vuser2-new', 'TG', self.dist_token)
        self.checkAddVpnuserApiRequest('vuser2-new@example.com', 'EM', self.dist_token)

    def checkCreateOutlineUserApiRequest(self, user, token=None, dist_model=0):
        url = reverse('modify-outline-user')
        data = {
            'user': user.username,
            'dist_model': dist_model,
            'request_type': 'legacy'
        }

        if token:
            response = self.client.put(url, data=data, HTTP_AUTHORIZATION=f'Token {token}')
        else:
            response = self.client.put(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)
        outuser = response.json()

        aftuser = OutlineUser.objects.get(user__username=user.username, removed=False)
        self.assertEqual(outuser['id'], aftuser.id)
        self.assertEqual(outuser['reputation'], aftuser.reputation)
        self.assertIsNone(outuser['transfer'])
        self.assertIsNone(outuser['user_issue'])
        self.assertEqual(outuser['user'], aftuser.user.username)
        self.assertIsNone(aftuser.transfer)
        self.assertIsNone(aftuser.user_issue)

        aftuser_keys = aftuser.user.get_keys()
        self.assertEqual(len(outuser['created_keys']), len(aftuser_keys))
        for okey in outuser['created_keys']:
            found = False
            for akey in aftuser_keys:
                if okey['outline_key'] == akey.outline_key:
                    self.assertEqual(okey['server'], akey.server.id)
                    self.assertEqual(okey['outline_key_id'], akey.outline_key_id)
                    found = True
                    break
            self.assertTrue(found)

    def testCreateOutlineUserApiAnonRequest(self):
        url = reverse('retrieve-vpn-user', args=[self.ouser1.user.username])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testCreateOutlineUserApiDistributorRequest(self):
        self.checkCreateOutlineUserApiRequest(self.vuser1, self.dist_token)
        self.checkCreateOutlineUserApiRequest(self.vuser2, self.dist_token)
        self.checkCreateOutlineUserApiRequest(self.vuser1, self.dist_token, dist_model=1)
        self.checkCreateOutlineUserApiRequest(self.vuser2, self.dist_token, dist_model=1)

    def testCreateOutlineUserApiDistributorAdminRequest(self):
        self.checkCreateOutlineUserApiRequest(self.vuser1, self.distadmin_token)
        self.checkCreateOutlineUserApiRequest(self.vuser2, self.distadmin_token)
        self.checkCreateOutlineUserApiRequest(self.vuser1, self.distadmin_token, dist_model=1)
        self.checkCreateOutlineUserApiRequest(self.vuser2, self.distadmin_token, dist_model=1)

    def checkRetrieveOutlineUserApiRequest(self, user, token=None):
        url = reverse('retrieve-outline-user', args=[user.user.username])

        if token:
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
        else:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        outuser = response.json()
        self.assertEqual(outuser['id'], user.id)
        self.assertEqual(outuser['reputation'], user.reputation)
        self.assertEqual(outuser['transfer'], user.transfer)
        self.assertEqual(outuser['user_issue'], user.user_issue)
        self.assertEqual(outuser['user'], user.user.username)

    def testRetrieveOutlineUserApiAnonRequest(self):
        url = reverse('retrieve-vpn-user', args=[self.ouser1.user.username])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveOutlineUserApiDistributorRequest(self):
        self.checkRetrieveOutlineUserApiRequest(self.ouser1, self.dist_token)
        self.checkRetrieveOutlineUserApiRequest(self.ouser2, self.dist_token)

    def testRetrieveOutlineUserApiDistributorAdminRequest(self):
        self.checkRetrieveOutlineUserApiRequest(self.ouser1, self.distadmin_token)
        self.checkRetrieveOutlineUserApiRequest(self.ouser2, self.distadmin_token)

    def checkRetrieveVpnUserList(self, token):
        url = reverse('list-vpn-users')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)
        content = response.content.decode('utf-8')
        reader = csv.DictReader(StringIO(content), skipinitialspace=True)

        count = 0
        for row in reader:
            count += 1
            vpnuser = Vpnuser.objects.filter(username=row['username'])
            self.assertEqual(vpnuser.count(), 1)
            vpnuser = vpnuser.first()
            self.assertEqual(row['channel'], vpnuser.channel)
            self.assertEqual(int(row['reputation']), vpnuser.reputation)
            self.assertEqual(row['delete_date'], vpnuser.delete_date if vpnuser.delete_date else '')
            self.assertEqual(str2bool(row['banned']), vpnuser.banned)
            self.assertEqual(int(row['banned_reason']), vpnuser.banned_reason)
            keys = get_key_dict(vpnuser.get_keys())
            for k in keys:
                k.pop('id')
            self.assertEqual(
                json.loads(row['outline_key']),
                keys)
            self.assertEqual(
                json.loads(row['region']),
                list(vpnuser.region.values_list('id', flat=True)))

        self.assertEqual(Vpnuser.objects.count(), count)

    def testRetrieveVpnUserListAnonRequest(self):
        url = reverse('list-vpn-users')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveVpnUserListDistributerRequest(self):
        self.checkRetrieveVpnUserList(self.dist_token)
        self.checkRetrieveVpnUserList(self.distadmin_token)

    def checkRetrieveIssueList(self, token):
        url = reverse('list-issues')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)
        response = response.json()
        issues = Issue.objects.all()
        self.assertEqual(issues.count(), response['count'])
        results = response['results']
        for result in results:
            issue = Issue.objects.filter(id=result['id'])
            self.assertEqual(issue.count(), 1)
            self.assertEqual(issue.title, result['title'])
            self.assertEqual(issue.description, result['description'])
            self.assertEqual(issue.description_en, result['description_en'])
            self.assertEqual(issue.description_fa, result['description_fa'])
            self.assertEqual(issue.description_ar, result['description_ar'])

    def testRetrieveIssueListAnonRequest(self):
        url = reverse('list-issues')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveIssueListDistributerRequest(self):
        self.checkRetrieveIssueList(self.dist_token)

    def testRetrieveIssueListDistributerAdminRequest(self):
        self.checkRetrieveIssueList(self.distadmin_token)

    def checkRetrieveAccountDeleteReasonList(self, token):
        url = reverse('list-delete-reasons')
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)
        response = response.json()
        reasons = AccountDeleteReason.objects.all()
        self.assertEqual(reasons.count(), response['count'])
        results = response['results']
        for result in results:
            reason = AccountDeleteReason.objects.filter(id=result['id'])
            self.assertEqual(reason.count(), 1)
            self.assertEqual(reason.description, result['description'])
            self.assertEqual(reason.description_en, result['description_en'])
            self.assertEqual(reason.description_fa, result['description_fa'])
            self.assertEqual(reason.description_ar, result['description_ar'])

    def testRetrieveAccountDeleteReasonListAnonRequest(self):
        url = reverse('list-delete-reasons')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveAccountDeleteReasonListDistributerRequest(self):
        self.checkRetrieveAccountDeleteReasonList(self.dist_token)

    def testRetrieveAccountDeleteReasonListDistributerAdminRequest(self):
        self.checkRetrieveAccountDeleteReasonList(self.distadmin_token)

    def checkRetrieveOutlineUserList(self, token):
        try:
            url = reverse('list-outline-users')
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {token}')
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.content)
            content = response.content.decode('utf-8')
            reader = csv.DictReader(StringIO(content), skipinitialspace=True)
        except Exception as exc:
            from django.http import HttpRequest
            from distribution.views import OutlineUserList

            print(f'Outline User List is not enabled, using view directly! ({str(exc)})')
            request = HttpRequest()
            request.META['HTTP_AUTHORIZATION'] = f'Token {token}'
            request.method = 'GET'
            reader = OutlineUserList.as_view()(request=request).data

        count = 0
        for row in reader:
            count += 1
            outlineuser = OutlineUser.objects.filter(id=int(row['id']))
            self.assertEqual(outlineuser.count(), 1)
            outlineuser = outlineuser.first()
            self.assertEqual(row['user'], outlineuser.user.username)
            self.assertEqual(int(row['server']), outlineuser.server.id)
            self.assertEqual(row['outline_key'], outlineuser.outline_key)
            self.assertEqual(int(row['reputation']), outlineuser.reputation)
            self.assertEqual(int(row['transfer']) if row['transfer'] else None, outlineuser.transfer)
            self.assertEqual(int(row['user_issue']) if row['user_issue'] else None, outlineuser.user_issue)

        self.assertEqual(OutlineUser.objects.count(), count)

    def testRetrieveOutlineUserListAnonRequest(self):
        try:
            url = reverse('list-outline-users')
        except Exception:
            return
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def testRetrieveOutlineUserListDistributerRequest(self):
        self.checkRetrieveOutlineUserList(self.dist_token)

    def testRetrieveOutlineUserListDistributerAdminRequest(self):
        self.checkRetrieveOutlineUserList(self.distadmin_token)


class ServerSelectionTests(TestCase):

    def setUp(self):
        self.region_iran = baker.make_recipe('preference.region_iran')
        self.server1 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='100.100.100.100',
            name='TG 100',
            level=10,
            region=[self.region_iran],
            type='legacy')
        self.server2 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='111.111.111.111',
            name='TG 111',
            level=10,
            region=[self.region_iran],
            type='legacy')
        self.server3 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='121.121.121.121',
            name='TG 121',
            level=10,
            region=[self.region_iran],
            type='legacy')
        self.server4 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='131.131.131.131',
            name='TG 131',
            level=10,
            region=[self.region_iran],
            type='legacy')

    def testServerSelection(self):
        print('Testing Server selection algorithm takes longer, be patient...')
        for i in range(40):
            vuser = Vpnuser.objects.create(
                username=f'user_40_{i}',
                channel='TG',
                reputation=0)
            vuser.region.add(self.region_iran)
            OutlineUser.objects.create(
                user=vuser,
                server=self.server1,
                active=True,
                removed=False,
                outline_key=f'https://test.test.test/key_40_{i}',
                outline_key_id=f'{i}'
            )
        for i in range(20):
            vuser = Vpnuser.objects.create(
                username=f'user_20_{i}',
                channel='TG',
                reputation=0)
            vuser.region.add(self.region_iran)
            OutlineUser.objects.create(
                user=vuser,
                server=self.server2,
                active=True,
                removed=False,
                outline_key=f'https://test.test.test/key_20_{i}',
                outline_key_id=f'{i}'
            )
        for i in range(20):
            vuser = Vpnuser.objects.create(
                username=f'user_20_INACTIVE_{i}',
                channel='TG',
                reputation=0)
            vuser.region.add(self.region_iran)
            OutlineUser.objects.create(
                user=vuser,
                server=self.server2,
                active=False,
                removed=False,
                outline_key=f'https://test.test.test/key_20_{i}',
                outline_key_id=f'{i}'
            )
        for i in range(10):
            vuser = Vpnuser.objects.create(
                username=f'user_10_{i}',
                channel='TG',
                reputation=0)
            vuser.region.add(self.region_iran)
            OutlineUser.objects.create(
                user=vuser,
                server=self.server3,
                active=True,
                removed=False,
                outline_key=f'https://test.test.test/key_10_{i}',
                outline_key_id=f'{i}'
            )
        for i in range(30):
            vuser = Vpnuser.objects.create(
                username=f'user_10_REMOVED_{i}',
                channel='TG',
                reputation=0)
            vuser.region.add(self.region_iran)
            OutlineUser.objects.create(
                user=vuser,
                server=self.server3,
                active=True,
                removed=True,
                outline_key=f'https://test.test.test/key_10_{i}',
                outline_key_id=f'{i}'
            )
        for i in range(5):
            vuser = Vpnuser.objects.create(
                username=f'user_05_{i}',
                channel='TG',
                reputation=0)
            vuser.region.add(self.region_iran)
            OutlineUser.objects.create(
                user=vuser,
                server=self.server4,
                active=True,
                removed=False,
                outline_key=f'https://test.test.test/key_05_{i}',
                outline_key_id=f'{i}'
            )
        for i in range(35):
            vuser = Vpnuser.objects.create(
                username=f'user_05_INACTIVE_REMOVED_{i}',
                channel='TG',
                reputation=0)
            vuser.region.add(self.region_iran)
            OutlineUser.objects.create(
                user=vuser,
                server=self.server4,
                active=False,
                removed=True,
                outline_key=f'https://test.test.test/key_05_{i}',
                outline_key_id=f'{i}'
            )

        self.assertEqual(OutlineUser.objects.filter(server=self.server1, removed=False, active=True).count(), 40)
        self.assertEqual(OutlineUser.objects.filter(server=self.server2, removed=False, active=True).count(), 20)
        self.assertEqual(OutlineUser.objects.filter(server=self.server3, removed=False, active=True).count(), 10)
        self.assertEqual(OutlineUser.objects.filter(server=self.server4, removed=False, active=True).count(), 5)

        ser = OutlineuserSerializer()
        vuser = Vpnuser.objects.create(
            username=f'user_new',
            channel='TG',
            reputation=0)
        vuser.region.add(self.region_iran)
        result = {}
        COUNT = 5000
        for i in range(COUNT):
            server = ser.get_server(vuser, 10, 0)
            self.assertEqual(len(server), 1)
            result[server[0].id] = result[server[0].id] + 1 if server[0].id in result else 1
        print(result)
        PART = float(COUNT) / 15.0
        self.assertLessEqual(abs(result[self.server4.id] - 8.0 * PART), 0.2 * 8.0 * PART)
        self.assertLessEqual(abs(result[self.server3.id] - 4.0 * PART), 0.2 * 4.0 * PART)
        self.assertLessEqual(abs(result[self.server2.id] - 2.0 * PART), 0.2 * 2.0 * PART)
        self.assertLessEqual(abs(result[self.server1.id] - 1.0 * PART), 0.2 * 1.0 * PART)


class TestReputationSystem(TestCase):

    def setUp(self):
        self.region_iran = baker.make_recipe('preference.region_iran')

        location_us = baker.make_recipe('preference.location_us')
        location_ger = baker.make_recipe('preference.location_germany')
        location_fra = baker.make_recipe('preference.location_france')

        self.lserver1 = baker.make_recipe(
            'server.tg_loc_vpn_server',
            ipv4=f'210.10.10.10',
            name=f'TG REP 10',
            level=0,
            region=[self.region_iran],
            dist_model=1,
            location=location_us)
        self.lserver2 = baker.make_recipe(
            'server.tg_loc_vpn_server',
            ipv4=f'211.11.11.11',
            name=f'TG REP 11',
            level=0,
            region=[self.region_iran],
            dist_model=1,
            location=location_ger)
        self.lserver3 = baker.make_recipe(
            'server.tg_loc_vpn_server',
            ipv4=f'212.12.12.12',
            name=f'TG REP 12',
            level=0,
            region=[self.region_iran],
            dist_model=1,
            location=location_fra)

        self.basic_server3 = baker.make_recipe(
            'server.tg_vpn_server',
            ipv4='214.14.14.14',
            name='TG REP 14',
            level=2,
            region=[self.region_iran])

        self.vuser = baker.make_recipe(
            'distribution.vpnuser',
            channel='TG')

        self.vuser3 = baker.make_recipe(
            'distribution.vpnuser',
            channel='TG')

        self.ouser3 = baker.make_recipe(
            'distribution.outlineuser',
            user=self.vuser3,
            server=self.basic_server3)

        self.ouser41 = baker.make_recipe(
            'distribution.outlineuser',
            user=self.vuser,
            server=self.lserver1)
        self.ouser42 = baker.make_recipe(
            'distribution.outlineuser',
            user=self.vuser,
            server=self.lserver2)
        self.ouser43 = baker.make_recipe(
            'distribution.outlineuser',
            user=self.vuser,
            server=self.lserver3)

    def testBasicReputationIncrease(self):
        vuser = self.ouser3.user
        oserver = self.ouser3.server

        oserver.is_blocked = False
        oserver.is_distributing = True
        oserver.active = True
        oserver.save()
        self.assertTrue(oserver.is_working())

        ser = OutlineuserSerializer()
        self.assertTrue(ser.increase_reputation(vuser, dist_model=0))

        oserver.is_blocked = True
        oserver.save()
        self.assertFalse(ser.increase_reputation(vuser, dist_model=0))
        oserver.is_blocked = False

        oserver.is_distributing = False
        oserver.save()
        self.assertFalse(ser.increase_reputation(vuser, dist_model=0))
        oserver.is_distributing = True

        oserver.active = False
        oserver.save()
        self.assertFalse(ser.increase_reputation(vuser, dist_model=0))
        oserver.active = True

        oserver.save()

    def testLocationBaseReputationIncrease(self):
        ser = OutlineuserSerializer()

        self.lserver1.is_blocked = False
        self.lserver1.is_distributing = True
        self.lserver1.active = True
        self.lserver1.save()
        self.assertTrue(self.lserver1.is_working())

        self.lserver2.is_blocked = False
        self.lserver2.is_distributing = True
        self.lserver2.active = True
        self.lserver2.save()
        self.assertTrue(self.lserver2.is_working())

        self.lserver3.is_blocked = False
        self.lserver3.is_distributing = True
        self.lserver3.active = True
        self.lserver3.save()
        self.assertTrue(self.lserver3.is_working())

        self.assertTrue(ser.increase_reputation(self.vuser, dist_model=1))

        self.lserver1.is_blocked = True
        self.lserver1.save()
        self.assertFalse(self.lserver1.is_working())
        self.assertTrue(ser.increase_reputation(self.vuser, dist_model=1))

        self.lserver2.is_blocked = True
        self.lserver2.save()
        self.assertFalse(self.lserver2.is_working())
        self.assertTrue(ser.increase_reputation(self.vuser, dist_model=1))

        self.lserver3.is_blocked = True
        self.lserver3.save()
        self.assertFalse(self.lserver3.is_working())
        self.assertFalse(ser.increase_reputation(self.vuser, dist_model=1))
