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

from django.core.exceptions import ValidationError
from django.db import models

from preference.models import (
    Region,
    Location)


USER_SRC_CHOICES = (
    ('TG', 'Telegram'),
    ('EM', 'Email'),
    ('SG', 'Signal'),
    ('NA', 'Unknows')
)


class DistributionModelChoice(models.IntegerChoices):
    BASIC = 0, 'Basic'
    LOCATIONED = 1, 'Location Based'
    FIXED_IP = 2, 'Fixed IP'


class Server(models.Model):
    """
    Server information
    """
    class Meta:
        abstract = True

    name = models.CharField(
        max_length=128,
        unique=True)

    ipv4 = models.GenericIPAddressField(
        null=True,
        blank=True)

    ipv6 = models.GenericIPAddressField(
        null=True,
        blank=True)

    provider = models.CharField(
        max_length=128,
        null=True,
        blank=True)

    cost = models.FloatField(
        null=True,
        blank=True)

    user_src = models.CharField(
        choices=USER_SRC_CHOICES,
        max_length=2,
        default='NA')

    reputation = models.IntegerField(
        default=0)

    level = models.IntegerField(
        default=0)

    active = models.BooleanField(
        default=False)

    alert = models.BooleanField(
        default=False)

    is_blocked = models.BooleanField(
        default=False)

    is_distributing = models.BooleanField(
        default=True)

    region = models.ManyToManyField(
        Region,
        blank=True)

    dist_model = models.IntegerField(
        default=0,
        choices=DistributionModelChoice.choices,
        verbose_name='Distribution Model'
    )

    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def is_working(self) -> bool:
        """
        Is server in a working condition?

        :param server: A Server object
        :return: If the server is in a good state
        """
        if (not self.is_blocked and
                self.is_distributing and
                self.active):
            return True
        return False

    def clean(self):
        if self.ipv4 or self.ipv6:
            return
        raise ValidationError('Either IPv4 or IPv6 should be provided')

    def __str__(self):
        if self.name:
            return f'{self.id}: {self.name}'
        return f'{self.id}: {self.ipv4 if self.ipv4 else self.ipv6}'


class OutlineServer(Server):
    """
    Outline VPN servers
    """
    api_url = models.TextField(
        null=True,
        blank=True)
    api_cert = models.TextField(
        null=True,
        blank=True)
    prometheus_port = models.IntegerField(
        default=900)
    label = models.CharField(
        max_length=128,
        null=True,
        blank=True)
    type = models.CharField(
        max_length=64,
        choices=[
            ('legacy', 'Legacy'),
            ('central', 'Central'),
            ('gtf', 'GTF'),
        ],
        default='legacy')
