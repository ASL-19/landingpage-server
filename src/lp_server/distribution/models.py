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

import base64
import json
import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache
from django.db.utils import ProgrammingError
from django.conf import settings

from lp_server.models import DatedMixin
from server.models import (
    OutlineServer,
    DistributionModelChoice)
from preference.models import Region

from distribution.utils import base64_padding, put_file_on_S3

logger = logging.getLogger(__name__)

USER_CHANNEL_CHOICES = (
    ('TG', 'Telegram'),
    ('EM', 'Email'),
    ('SG', 'Signal'),
    ('NA', 'Unknown')
)


class AccountDeleteReason(models.Model):
    """
    To store users' reason to delete their accounts
    """
    description = models.TextField()
    created = models.DateTimeField(
        auto_now_add=True)

    def __str__(self):
        return self.description[:30]


class Issue(DatedMixin):
    """
    Model definition for Issues reported by users
    """
    title = models.CharField(
        max_length=128)
    description = models.CharField(
        max_length=256)

    def __str__(self):
        return self.title


class BannedReason(models.IntegerChoices):
    """
    Model definition for reasons a user is banned
    """

    NA = 0, 'Not banned'
    DELETED = 1, 'Account Deleted'
    SHARED = 2, 'Account Shared'
    ADMIN = 3, 'Admin Banned'
    API_UPDATE = 4, 'API Update'
    TORRENT = 5, 'Torrent'


class NotificationStatus(models.TextChoices):
    """
    Model notification status for Vpn Users Telegram notification
    """
    ENABLED = 'ENABLED', _('ENABLED')
    BLOCKED_BOT = 'BLOCKED_BOT', _('BLOCKED BOT')
    ACCOUNT_DEACTIVATED = 'ACCOUNT_DEACTIVATED', _('ACCOUNT DEACTIVATED')


class Vpnuser(DatedMixin):
    """
    Model definition for Vpn Users
    """

    username = models.CharField(
        max_length=256,
        blank=False,
        unique=True)
    channel = models.CharField(
        choices=USER_CHANNEL_CHOICES,
        max_length=2,
        default='NA')
    reputation = models.IntegerField(
        default=0)
    delete_date = models.DateTimeField(
        null=True,
        blank=True)
    delete_reason = models.ForeignKey(
        AccountDeleteReason,
        null=True,
        blank=True,
        on_delete=models.SET_NULL)
    banned = models.BooleanField(
        default=False)
    banned_reason = models.IntegerField(
        choices=BannedReason.choices,
        default=BannedReason.NA)
    userchat = models.CharField(
        max_length=256,
        null=True,
        blank=True
    )
    region = models.ManyToManyField(
        Region,
        blank=True
    )
    # Field for telegram bot blocked by user or deactivated telegram user accounts
    notification_status = models.CharField(
        _('Notification Status'),
        max_length=25,
        choices=NotificationStatus.choices,
        default=NotificationStatus.ENABLED,
        help_text=_('if the telegram bot is blocked or the telegram User account is deactivated')
    )

    def get_keys(self):
        """
        Returns user keys
        """
        try:
            last_key = self.outline_keys.filter(removed=False).latest('updated_date')
        except OutlineUser.DoesNotExist:
            return []
        if last_key:
            dist_model = last_key.server.dist_model
            if dist_model == DistributionModelChoice.LOCATIONED:
                if last_key.group_id:
                    keys = self.outline_keys.filter(removed=False, group_id=last_key.group_id)
                    return list(keys)
                else:
                    logger.error(f'Key {last_key.id} is location based with no group_id!')
                    return []
            elif dist_model == DistributionModelChoice.FIXED_IP:
                # TODO: Implement FIXED_IP
                return []
            else:       # dist_model == DistributionModelChoice.BASIC:
                return [last_key]

    def __str__(self):
        return self.username


class DeletionCause(models.TextChoices):
    """
    Cause of deletion choices
    """

    NA = 'NA', _('Not applicable')
    INACTIVE = 'INACTIVE', _('Inactive Key Removal')


class OutlineUser(DatedMixin):
    """
    Model definition for OutlineUser.
    """
    user = models.ForeignKey(
        Vpnuser,
        null=True,
        blank=True,
        related_name='outline_keys',
        on_delete=models.SET_NULL)

    server = models.ForeignKey(
        OutlineServer,
        on_delete=models.PROTECT,
        related_name='users')

    outline_key_id = models.IntegerField()

    outline_key = models.CharField(
        max_length=512)

    reputation = models.IntegerField(
        default=0)

    transfer = models.FloatField(
        null=True,
        blank=True)

    user_issue = models.ForeignKey(
        Issue,
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    active = models.BooleanField(
        default=True
    )

    removed = models.BooleanField(
        default=False)

    exists_on_server = models.BooleanField(
        default=True)

    group_id = models.BigIntegerField(
        null=True,
        blank=True
    )

    delete_date = models.DateTimeField(
        null=True,
        blank=True)

    deletion_cause = models.CharField(
        _('Deletion Cause'),
        max_length=10,
        choices=DeletionCause.choices,
        default=DeletionCause.NA,
        editable=False)

    request_type = models.CharField(
        _('Request Type'),
        max_length=128,
        default='legacy',
        editable=False)

    def deactivate(self, issue, transfer):
        if self.request_type == 'legacy':
            self.user_issue = issue
            self.transfer = transfer
            self.removed = True
            self.delete_date = None
            self.deletion_cause = DeletionCause.NA
            self.save()

    def reactivate(self):
        if self.request_type == 'legacy':
            self.user_issue = None
            self.transfer = None
            self.removed = False
            self.delete_date = None
            self.deletion_cause = DeletionCause.NA
            self.save()

    def __str__(self):
        return self.outline_key

    class Meta:
        verbose_name = 'OutlineUser'
        verbose_name_plural = 'OutlineUsers'


class OnlineConfig(DatedMixin):
    """
    Model definition for OnlineConfig.
    """
    file_name = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        unique=True)

    storage_service = models.CharField(
        max_length=64,
        blank=True,
        null=True)

    outline_user = models.ForeignKey(
        OutlineUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='online_configs')

    def __str__(self):
        return (f'{self.outline_user}:{self.storage_service}')

    def update_json_file(self, ss_link, prefix_str=None):
        """
        Create or Update the SSconfig file
        """
        key_name = f'{self.file_name}.json'
        logger.debug(f'Updating {key_name} on S3 bucket')

        logger.debug(ss_link)
        ss_link = ss_link[5:].split("/")[0]
        ss_link = ss_link.split("@")
        ss_ip_port = ss_link[1].split(":")
        server_port = ss_ip_port[1] if '?' not in ss_ip_port[1] else ss_ip_port[1].split('?')[0]
        ss_decoded = base64.b64decode(base64_padding(ss_link[0]))
        ss_decoded = ss_decoded.decode("utf-8").split(":")
        ss_config_data = {
            "server": ss_ip_port[0],
            "server_port": server_port,
            "password": ss_decoded[1],
            "method": ss_decoded[0]
        }
        if prefix_str:
            ss_config_data["prefix"] = prefix_str

        try:
            put_file_on_S3(
                settings.S3_SSCONFIG_BUCKET_NAME,
                key_name,
                json.dumps(ss_config_data),
                content_type='application/json',
                cache_control=f'max-age={settings.S3_SSCONFIG_MAX_AGE}')

        except Exception as e:
            logger.error('Error in writing file {} on {} due to {}'.format(
                key_name,
                settings.S3_SSCONFIG_BUCKET_NAME,
                str(e)))
            raise

        ss_config_link = "ssconf://s3.amazonaws.com/{}/{}".format(settings.S3_SSCONFIG_BUCKET_NAME, key_name)
        logger.debug(f'SSconfig json file is ready: {ss_config_link}')


class Statistics(models.Model):
    """
    Model definition for Statistics
    """

    servers = models.IntegerField()

    countries = models.IntegerField()

    downloads = models.IntegerField()

    active_monthly_users = models.IntegerField()

    @classmethod
    def update(cls):
        from server.models import OutlineServer
        obj = cls.objects.get(pk=1)
        obj.servers = OutlineServer.objects.filter(
            is_blocked=False,
            is_distributing=True,
            active=True).count()
        obj.countries = OutlineServer.objects.distinct('location').count()
        obj.save()

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(Statistics, self).save(*args, **kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        if cache.get(cls.__class__.__name__) is None:
            try:
                obj, created = cls.objects.get_or_create(pk=1)
            except ProgrammingError:
                return None

            if created:
                obj.set_cache()
        return cache.get(cls.__class__.__name__)

    def set_cache(self):
        cache.set(self.__class__.__name__, self)


class Prefix(models.Model):
    """
    Model definition for prefix to use to mask the protocol
    """
    name = models.CharField(
        max_length=128,
        unique=True)
    port = models.IntegerField(
        null=True,
        blank=True)
    prefix_str = models.CharField(
        max_length=256)
    is_active = models.BooleanField(
        default=True)

    def __str__(self):
        return f'{self.prefix_str}: {self.port}'

    class Meta:
        verbose_name_plural = 'Prefixes'


class LoadBalancer(models.Model):
    """
    Model definition for pool containing HAProxy and VPN Servers
    """
    host_name = models.CharField(
        max_length=128)
    server = models.ForeignKey(
        OutlineServer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    is_active = models.BooleanField(
        default=True)
    replaces_ip = models.BooleanField(
        default=True,
        help_text=_('Doesn\'t apply to gtf servers'))

    def __str__(self):
        if self.server and self.server.name:
            return f'{self.host_name}: {self.server.name}'
        else:
            return f'{self.host_name}'

    class Meta:
        verbose_name_plural = 'Load Balancers'
