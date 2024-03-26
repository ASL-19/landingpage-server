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

import sys
import requests
import random
import secrets
import string
import json
import logging
import asyncio
from typing import List
from hashlib import sha512
from asgiref.sync import sync_to_async

from django.db.models import Count, Max, Q
from django.db import transaction
from django.db.models.query import QuerySet
from django.conf import settings

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.exceptions import APIException
from outline_api import Manager as OutlineManager
from outline_api.errors import (
    OutlineTimeoutError, DoesNotExistError)

from distribution.models import (
    Vpnuser,
    OutlineUser,
    USER_CHANNEL_CHOICES,
    Issue,
    AccountDeleteReason,
    Statistics,
    BannedReason,
    OnlineConfig,
    LoadBalancer,
    Prefix)
from distribution.utils import get_key_dict, replace_port, replace_ip
from lp_server.reputation import ReputationSystem
from server.models import (
    OutlineServer,
    DistributionModelChoice)
from preference.models import (
    Region,
    Location)

logger = logging.getLogger(__name__)


def hash_user_id(user_id):
    if user_id:
        if 'test' in sys.argv:
            return user_id
        return sha512(user_id.encode('utf-8')).hexdigest()


class NotAcceptable(APIException):
    """
    Custom Error to represent Unacceptable API calls
    """

    status_code = 406
    default_detail = 'Not Acceptable, try again later.'
    default_code = 'not_acceptable'


class VpnuserSerializer(serializers.Serializer):
    """
    Serializer for VPN Users
    """

    id = serializers.IntegerField(
        read_only=True)
    username = serializers.CharField(
        required=True,
        max_length=256,
        allow_blank=False,
        validators=[UniqueValidator(queryset=Vpnuser.objects.all())])
    channel = serializers.ChoiceField(
        choices=USER_CHANNEL_CHOICES,
        required=True)
    reputation = serializers.IntegerField(
        required=False,
        default=0)
    banned = serializers.BooleanField(
        required=False,
        default=False)
    banned_reason = serializers.IntegerField(
        required=False,
        read_only=True)
    outline_key = serializers.SerializerMethodField()
    userchat = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        default=None)
    region = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=Region.objects.all())
    delete_date = serializers.DateTimeField(
        read_only=True)

    def create(self, validated_data):
        """
        Create and return a new Vpnuser instance, given the validated data.
        """
        regions = validated_data.pop('region')
        userchat = validated_data.pop('userchat')
        if userchat:
            validated_data['userchat'] = hash_user_id(userchat)
        username = validated_data.pop('username')
        validated_data['username'] = hash_user_id(username)
        try:
            user = Vpnuser.objects.create(**validated_data)
        except Exception as exc:
            logger.error(f'Unable to add VPN user ({str(exc)})')
            raise serializers.ValidationError("The User cannot be created.")

        if regions:
            user.region.set(regions)
            user.save()

        return user

    def update(self, instance, validated_data):
        """
        Update and return an existing Vpnuser instance, given the validated data.
        """
        username = validated_data.get(
            'username',
            instance.username)
        instance.username = hash_user_id(username)
        instance.channel = validated_data.get(
            'channel',
            instance.channel)
        instance.reputation = validated_data.get(
            'reputation',
            instance.reputation)
        banned = validated_data.get(
            'banned',
            instance.banned)
        if banned != instance.banned:
            instance.banned = banned
            if banned:
                instance.banned_reason = BannedReason.API_UPDATE
            else:
                instance.banned_reason = BannedReason.NA
        userchat = validated_data.get(
            'userchat',
            None)
        if userchat:
            hashed_userchat = hash_user_id(userchat)
            if hashed_userchat != instance.userchat:
                instance.userchat = hashed_userchat
        region_list = validated_data.get('region', [])
        if len(region_list) > 0:
            instance.region.clear()
            for reg in region_list:
                instance.region.add(reg)

        instance.save()
        return instance

    def get_outline_key(self, user):
        """
        Populate Outline Key

        :param user: Vpnuser object to get their keys
        :return: List of user keys
        """
        return get_key_dict(user.get_keys())


class VpnuserStringSerializer(VpnuserSerializer):

    outline_key = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()

    def get_region(self, user):
        """
        Populate regions
        """
        return json.dumps(list(user.region.values_list('id', flat=True)))

    def get_outline_key(self, user):
        """
        Populate Outline Key

        :param user: Vpnuser object to get their keys
        :return: List of user keys
        """
        keys_list = []
        keys = user.get_keys()
        if keys:
            for key in keys:
                keys_list.append({
                    'outline_key_id': key.outline_key_id,
                    'server': key.server.id,
                    'outline_key': key.outline_key
                })
        return json.dumps(keys_list)


class OutlineKeySerializer(serializers.Serializer):
    """
    Serializer for outline keys
    """

    server = serializers.IntegerField(
        read_only=True)
    outline_key_id = serializers.IntegerField(
        required=False)
    outline_key = serializers.CharField(
        required=False,
        max_length=256)


class OutlineuserSerializer(serializers.Serializer):
    """
    Serializer for Outline User
    """

    id = serializers.IntegerField(
        read_only=True)
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username')
    created_keys = OutlineKeySerializer(
        read_only=True,
        many=True)
    reputation = serializers.IntegerField(
        default=0)
    transfer = serializers.FloatField(
        required=False)
    user_issue = serializers.PrimaryKeyRelatedField(
        read_only=True,
        required=False)
    user = serializers.CharField()
    model = serializers.IntegerField(
        required=False,
        write_only=True)
    server = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    outline_key = serializers.CharField(
        read_only=True
    )
    exists_on_server = serializers.BooleanField(
        read_only=True)
    request_type = serializers.CharField(
        required=False
    )
    ss_link = serializers.SerializerMethodField()

    def get_ss_link(self, user):
        try:
            if user.online_configs.last():
                file_name = user.online_configs.last().file_name
                if settings.REAL_VPN_SERVERS:
                    ss_config_link = f'ssconf://s3.amazonaws.com/{settings.S3_SSCONFIG_BUCKET_NAME}/{file_name}.json'
                else:
                    ss_config_link = f'ssconf://s3.amazonaws.com/<S3_SSCONFIG_BUCKET_NAME>/{file_name}.json'
                return ss_config_link
            else:
                return None
        except OnlineConfig.DoesNotExist:
            return None

    def get_server_by_level(
            self,
            user,
            level,
            limited,
            exclude,
            dist_model,
            location=None) -> QuerySet:
        """
        Returns servers queryset based on level

        :param user: Vpnuser object to get servers for
        :param level: Server level
        :param limited: Boolean to indicate if we can use higher level servers, True = not use
        :param exclude: Boolean to indicate if we should exclude previous servers
        :param dist_mode: Distribution Model of the server
        :param location: If servers should be in a specific location
        :return: List of servers annotated by number of users
        """
        if limited:
            servers = OutlineServer.objects.filter(
                type='legacy',
                active=True,
                is_distributing=True,
                level=level,
                dist_model=dist_model,
                user_src=user.channel)
        else:
            servers = OutlineServer.objects.filter(
                type='legacy',
                active=True,
                is_distributing=True,
                level__gt=level,
                dist_model=dist_model,
                user_src=user.channel)
        if location:
            servers = servers.filter(
                location=location
            )
        if exclude:
            last_keys = OutlineUser.objects.filter(user=user).all()
            last_servers = list(set([last_key.server.id for last_key in last_keys]))
            servers = servers.exclude(
                id__in=last_servers)

        return servers.annotate(
            usercount=Count(
                'users',
                filter=Q(users__active=True, users__removed=False),
                distinct=True
            )).order_by('-usercount')

    def find_server(self, servers) -> OutlineServer:
        """
        Finds and return a server from the list
        based on number of users

        :param servers: List of servers to choose from
        :return: A server chosen based on algorithm
        """
        count = servers.count()
        if count > 1:
            inverse_total = 0
            for server in servers:
                if server.usercount == 0:
                    return server
                inverse_total += 1 / server.usercount
            prob = random.randint(0, 100)
            for server in servers:
                prob -= ((1 / server.usercount) * (1 / inverse_total)) * 100
                if prob <= 0:
                    break
        else:
            server = servers.first()

        return server

    def get_server(self, user, level, dist_model, location=None) -> List[OutlineServer]:
        """
        Get a server based on user's level and channel

        In case there is no server for the user to get
        we are going to return a server from the last
        level from servers that they have already received.

        :param user: Vpnuser to get servers for
        :param level: Server level
        :param dist_model: Distribution Model of the server
        :param location: If servers should be in a specific location
        :return: A list of servers to choose from
        """
        server_list = []
        locations = [location]
        if dist_model == DistributionModelChoice.LOCATIONED:
            locations = Location.objects.filter(active=True)

        for loc in locations:
            for exclude in [True, False]:           # exclude user's previous servers
                for limited in [True, False]:       # get servers in any level less then user's level
                    servers = self.get_server_by_level(
                        user,
                        level,
                        limited,
                        exclude,
                        dist_model,
                        loc.id if loc else None)
                    server = self.find_server(servers)
                    if server is not None:
                        break
                if server is not None:
                    break
            if server is None:
                logger.error(f'Unable to find a server for user {user.id} level {level} limited {limited}')
            else:
                server_list.append(server)

        return server_list

    def increase_reputation(self, user, dist_model) -> bool:
        """
        Should we increase user's reputation?

        :param user: Vpnuser object
        :param dist_model: Distrubution Model of the server
        :return: If we should affect reputation or not
        """
        if dist_model == DistributionModelChoice.LOCATIONED:
            if len(user.outline_keys.all()) == 0:
                return False
            for key in user.outline_keys.all():
                if key:
                    """
                    We don't increase reputation if at least one of the
                    servers is not working
                    """
                    if key.server and key.server.is_working():
                        return True
            return False
        elif dist_model == DistributionModelChoice.FIXED_IP:
            # TODO: implement fixed ip
            return False
        else:       # dist_model == DistributionModelChoice.BASIC
            if user.outline_keys:
                outline_user = user.outline_keys.first()
                if outline_user:
                    return outline_user.server and outline_user.server.is_working()
            return False

    @staticmethod
    async def _outline_manager_delete_key(api_url, api_cert, outline_key_id):
        """
        Asynchronously delete a key from server

        :param api_url: Outline Server's API URL
        :param api_cert: Outline Server's API Certificate
        :param outline_key_id: Outline Key ID
        :return: A list of OutlineUser ids of failed to be deleted keys
        """
        manager = OutlineManager(apiurl=api_url, apicrt=api_cert, timeout=settings.OUTLINE_TIMEOUT)
        await sync_to_async(manager.delete, thread_sensitive=True)(outline_key_id)

    @staticmethod
    def remove_key_from_server(keys) -> list:  # noqa: C901
        """
        Removes keys from server

        :param keys: A dict of keys to be removed from server
        :return: A list of OutlineUser ids of failed to be deleted keys
        """
        failed_keys = []
        for key in keys:
            id = key['id']
            if settings.REAL_VPN_SERVERS:
                server = key['server']
                outline_key_id = key['outline_key_id']
                server = OutlineServer.objects.get(id=server)

                # Removing key created using GTF API
                if server.type == 'gtf':
                    api_url = server.api_url
                    # Remove trailing slash at the end of the api url
                    if api_url.endswith('/'):
                        api_url = api_url[:-1]

                    url = f'{api_url}/{outline_key_id}'
                    response = requests.request("DELETE", url)
                    if response.status_code == 404:
                        logger.info(f'Key ({server}:{outline_key_id}) already removed from server')
                        OutlineUser.objects.filter(id=id).update(exists_on_server=False)
                    elif response.status_code == 200:
                        logger.info(f'Deleted key ({server}:{outline_key_id})')
                        OutlineUser.objects.filter(id=id).update(exists_on_server=False)
                    else:
                        failed_keys.append(id)
                        errmsg = f'Deleting key ({server}:{outline_key_id}) failed: status code {response.status_code}'
                        logger.error(errmsg)

                # Removing key created using Central or Legacy system
                # Skip calling inactive servers
                if server.active is False:
                    OutlineUser.objects.filter(id=id).update(exists_on_server=False)
                    continue

                try:
                    logger.info(f'Deleting key ({server}:{outline_key_id})')
                    asyncio.run(__class__._outline_manager_delete_key(
                        server.api_url,
                        server.api_cert,
                        outline_key_id))
                    OutlineUser.objects.filter(id=id).update(exists_on_server=False)
                except OutlineTimeoutError as e:
                    failed_keys.append(id)
                    errmsg = (
                        f'Deleting key ({server}:{outline_key_id}) timed out: '
                        f'{e.error_code} | {e.message}')
                    logger.error(errmsg)
                except DoesNotExistError as e:
                    errmsg = (
                        f'Deleting key ({server}:{outline_key_id}) failed '
                        'as it was not found on the server: '
                        f'{e.error_code} | {e.message}')
                    logger.warning(errmsg)
                    OutlineUser.objects.filter(id=id).update(exists_on_server=False)
                except Exception as exc:
                    failed_keys.append(id)
                    errmsg = f'Deleting key ({server}:{outline_key_id}) failed: {exc}'
                    logger.error(errmsg)
            else:
                OutlineUser.objects.filter(id=id).update(exists_on_server=False)
            errmsg = (
                f"{'Skipped' if not settings.REAL_VPN_SERVERS else ''} "
                f"Key {key['outline_key_id']} removed from server")
            logger.info(errmsg)

        return failed_keys

    @staticmethod
    async def _outline_manager_create_key(server):
        """
        Create key on an Outline Server

        :param server: Outline Server used to create key
        :return: New created Outline Key
        """
        manager = OutlineManager(apiurl=server.api_url, apicrt=server.api_cert, timeout=settings.OUTLINE_TIMEOUT)
        if server.label:
            new_key = await sync_to_async(manager.new, thread_sensitive=True)(server.label)
        else:
            new_key = await sync_to_async(manager.new, thread_sensitive=True)()

        return new_key

    @staticmethod
    def create_key_on_server(server) -> dict:
        """
        Create a key on the server

        :param server: The server to create the key on
        :return: New key created
        """
        if not settings.REAL_VPN_SERVERS:
            new_key = {
                'id': random.randint(1, 100),
                'accessUrl': f'https://localserver{random.randint(1, 100)}/api'
            }
        else:
            try:
                new_key = asyncio.run(__class__._outline_manager_create_key(server))
            except Exception as exc:
                logger.error(f'Unable to get new key from server {server.id} ({str(exc)})')
                raise NotAcceptable('Outline server error')
            if new_key is None:
                logger.error(f'Unable to get new key from server (NoneType) {server.id}')
                raise NotAcceptable('Outline server error')
        logger.info(f"{'Skipped' if not settings.REAL_VPN_SERVERS else ''} Key {new_key['id']} created on {server.id}")
        return new_key

    @staticmethod
    def remove_keys_from_db(keys, user_issue=None) -> None:
        """
        Inactivate keys on the db and update its data

        :param keys: A list of keys to be deactivated
        :param user_issue: Issue ID of the reason for removing the key
        :return: None
        """
        if user_issue:
            try:
                user_issue = Issue.objects.get(id=user_issue)
            except Issue.DoesNotExist:
                logger.error('Invalid issue specified!')
                user_issue = None

        if keys:
            for key in keys:
                transfer = None
                key.refresh_from_db()
                key.deactivate(user_issue, transfer)

    def unremove_lastkey_from_db(self, keys) -> None:
        """
        Reactivate keys in the db

        :param keys: List of OutlineUser keys to be reactivated
        :return: None
        """
        if keys:
            for key in keys:
                key.reactivate(key)

    def create_keys_gtf(self, user, server):
        """
        Create keys using GTF API

        :param user: Vpnuser for whom we create keys
        :return: outline_key_id and outline_key needed to create OutlineUser
        """

        api_url = server.api_url
        # Remove trailing slash at the end of the api url
        if api_url.endswith('/'):
            api_url = api_url[:-1]

        response = requests.request("GET", api_url)
        if response.status_code == 200:
            key_id = json.loads(response.content)['id']
            access_url_request = f'{api_url}/{key_id}/?format=url'
            access_url = requests.request("GET", access_url_request)

            return key_id, access_url.text

        else:
            raise Exception(f'Could not create keys using GTF API for {user}, status code {response.status_code}')

    def create_keys(self, user, request_type, validated_data, created_keys) -> object:  # noqa: C901
        """
        Create keys on the server and in the db

        :param user: Vpnuser for whom we create keys
        :param request_type: System on which to create keys (legacy, central, gtf...)
        :param validated_data: Data to pass to OutlineUser to create keys
        :param created_keys: List of created_keys on the server
        :return: An OutlineUser object + created keys to be serialized
        """

        # Creating keys using Legacy servers
        if request_type == 'legacy':
            group_id = None
            dist_model = validated_data.pop('model', DistributionModelChoice.BASIC)
            if dist_model == DistributionModelChoice.LOCATIONED:
                group_id = OutlineUser.objects.aggregate(max=Max('group_id'))['max']
                group_id = int(group_id) + 1 if group_id else 1

            new_rep = user.reputation
            if self.increase_reputation(user, dist_model):
                new_rep = ReputationSystem.after_new_key(user.reputation)
            level = ReputationSystem.server_level(new_rep)

            server_list = self.get_server(user, level, dist_model)
            if not server_list:
                raise NotAcceptable('No server found for user {}'.format(str(user.id)))

            outline_user = None
            for server in server_list:
                try:
                    new_key = __class__.create_key_on_server(server)
                    outline_key_id = new_key['id']
                    outline_key = new_key['accessUrl']
                except Exception as exc:
                    logger.error(f'Outline key creation error ({str(exc)})')
                    raise NotAcceptable('Outline key creation error')

                prefix_str = None
                try:
                    random_prefix = random.choice(Prefix.objects.filter(is_active=True))
                    prefix_str = random_prefix.prefix_str
                    outline_key = replace_port(outline_key, random_prefix.port)
                except Exception as exc:
                    logger.info(f'Active prefix to use for server {server} not found ({str(exc)})')

                validated_data['outline_key_id'] = outline_key_id
                validated_data['outline_key'] = outline_key
                created_keys.append({
                    'server': server.id,
                    'outline_key_id': outline_key_id,
                    'outline_key': outline_key,
                    'exists_on_server': True
                })

                outline_user = OutlineUser.objects.create(
                    **validated_data,
                    user=user,
                    server=server,
                    group_id=group_id,
                    reputation=new_rep,
                    request_type=request_type)

            if outline_user:
                outline_user.created_keys = created_keys
                logger.info(f'Successfully created key for user {user} with key_id {outline_user.outline_key_id}')

            if new_rep != user.reputation:
                user.reputation = new_rep
                user.save()

            return outline_user, prefix_str

        # Creating keys using Central Server
        elif request_type == 'central':
            try:
                # TODO: add a method to choose central server once multiple central servers are enabled
                server = random.choice(
                    OutlineServer.objects.filter(
                        type='central',
                        active=True,
                        is_distributing=True))
            except:
                raise NotAcceptable(f'No central server found for {user}')

            outline_user = None
            try:
                new_key = __class__.create_key_on_server(server)
                outline_key_id = new_key['id']
                outline_key = new_key['accessUrl']
            except Exception as exc:
                logger.error(f'Outline key creation error ({str(exc)})')
                raise NotAcceptable('Outline key creation error')

        # Creating keys using GTF API
        elif request_type == 'gtf':
            try:
                server = random.choice(
                    OutlineServer.objects.filter(
                        type='gtf',
                        active=True,
                        is_distributing=True))
                outline_key_id, outline_key = self.create_keys_gtf(user, server)
                prefix_str = None
            except Exception as exc:
                raise NotAcceptable(f'{exc}')

        else:
            raise NotAcceptable('Request type is not acceptable')

        random_loadbalancer = None
        try:
            random_loadbalancer = random.choice(LoadBalancer.objects.filter(server=server, is_active=True))
            if request_type != 'gtf':
                if random_loadbalancer.replaces_ip:
                    outline_key = replace_ip(new_key['accessUrl'], random_loadbalancer.host_name)
        except Exception as exc:
            logger.error(f'Active load balancer for server {server} not found ({str(exc)})')
            raise NotAcceptable(f'Active load balancer for server {server} not found ({str(exc)})')

        prefix_str = None
        try:
            random_prefix = random.choice(Prefix.objects.filter(is_active=True))
            prefix_str = random_prefix.prefix_str
            outline_key = replace_port(outline_key, random_prefix.port)
        except Exception as exc:
            logger.info(f'Active prefix to use for server {server} not found ({str(exc)})')

        validated_data['outline_key_id'] = outline_key_id
        validated_data['outline_key'] = outline_key
        created_keys.append({
            'server': server.id,
            'outline_key_id': outline_key_id,
            'outline_key': outline_key,
            'exists_on_server': True
        })

        outline_user = OutlineUser.objects.create(
            **validated_data,
            user=user,
            server=server,
            request_type=request_type)

        if outline_user:
            outline_user.created_keys = created_keys
            logger.info(f'Successfully created key for user {user} with key_id {outline_user.outline_key_id}')

        return outline_user, prefix_str

    def create(self, validated_data):  # noqa C901
        """
        Create and return a new OutlineUser instance, given the validated data.
        """
        user = validated_data.pop('user')
        user = hash_user_id(user)

        try:
            user = Vpnuser.objects.get(username=user)
        except Vpnuser.DoesNotExist:
            raise NotAcceptable('User does not exist')

        keys = OutlineUser.objects.filter(user=user).exclude(request_type='legacy')
        if keys:
            raise NotAcceptable('User already has a key')

        if user.banned:
            logger.info(f'User {user.id} is banned')
            raise NotAcceptable(f'User {user.id} is banned')

        # Choose a random request type with weighted choices
        # if the client doesn't provide one
        active_types = list(OutlineServer.objects.filter(active=True, is_distributing=True).distinct().values_list('type'))
        active_types_list = list(zip(*active_types))[0]

        if all(type in ['gtf', 'central'] for type in active_types_list) and len(active_types_list) == 2:
            if settings.REAL_VPN_SERVERS:
                gtf_weight = settings.GTF_PROB_WEIGHT
            else:
                gtf_weight = 50
            random_request_type = random.choices(['gtf', 'central'], weights=(gtf_weight, 100 - gtf_weight), k=1)[0]

        else:
            random_request_type = random.choices(active_types_list)[0]

        request_type = validated_data.pop('request_type', random_request_type)

        user_issue_id = validated_data.pop('user_issue', None)
        validated_data.pop('transfer', None)
        validated_data.pop('reputation', None)

        # Fetching all legacy keys associated to the user
        all_keys = user.outline_keys.filter(request_type='legacy')
        last_keys = list(all_keys)
        created_keys = []
        try:
            with transaction.atomic():
                outline_user, prefix_str = self.create_keys(user, request_type, validated_data, created_keys)

        except Exception as exc:
            """
                We have to revert object states - transaction reversal
                Does not revert django model states
            """
            # Revert Key created on the server
            if created_keys:
                __class__.remove_key_from_server(created_keys)
            logger.exception(f'Unable to create keys for user {user.id} Error: {exc}')
            raise NotAcceptable(f'Unable to create keys for user {user.id} - {exc}')

        logger.info(f'Ready to update Online Config with prefix: {prefix_str}')
        # Update OnlineConfig file
        if settings.REAL_VPN_SERVERS:
            try:
                online_config = OnlineConfig.objects.get(outline_user=outline_user)
                online_config.update_json_file(outline_user.outline_key, prefix_str)

            except OnlineConfig.DoesNotExist:
                file_name = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(64))
                online_config = OnlineConfig.objects.create(outline_user=outline_user, file_name=file_name, storage_service='s3')
                online_config.save()
                online_config.update_json_file(outline_user.outline_key, prefix_str)

        if last_keys:
            last_keys_list = get_key_dict(last_keys)
            __class__.remove_key_from_server(last_keys_list)
            __class__.remove_keys_from_db(last_keys, user_issue_id)

        return outline_user


class IssueSerializer(serializers.ModelSerializer):

    class Meta:
        model = Issue
        fields = '__all__'


class AccountDeleteReasonSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountDeleteReason
        fields = '__all__'


class OnlineConfigSerializer(serializers.ModelSerializer):

    ss_link = serializers.SerializerMethodField()

    def get_ss_link(self, config_file):
        try:
            file_name = config_file.file_name
            if settings.REAL_VPN_SERVERS:
                ss_config_link = f'ssconf://s3.amazonaws.com/{settings.S3_SSCONFIG_BUCKET_NAME}/{file_name}.json'
            else:
                ss_config_link = f'ssconf://s3.amazonaws.com/<S3_SSCONFIG_BUCKET_NAME>/{file_name}.json'
            return ss_config_link
        except OnlineConfig.DoesNotExist:
            return None

    class Meta:
        model = OnlineConfig
        fields = '__all__'


class StatisticsSerializer(serializers.ModelSerializer):

    countries_list = serializers.SerializerMethodField()

    def get_countries_list(self, obj):
        servers = OutlineServer.objects.distinct('location')
        return {
            'count': obj.countries,
            'list': [
                {
                    'flag': server.location.country.unicode_flag,
                    'code': server.location.country.code,
                    'name': server.location.country.name
                } if server.location is not None else {}
                for server in servers
            ]
        }

    class Meta:
        model = Statistics
        fields = [
            'servers',
            'countries_list',
            'downloads',
            'active_monthly_users'
        ]
