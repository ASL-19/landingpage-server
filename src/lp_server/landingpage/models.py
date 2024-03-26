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

from django.db import models
from django.utils import timezone

from server.models import OutlineServer
from publisher.models import Campaign
from landingpage.metrics import impression_counter


class LandingPage(models.Model):
    """
    Which server posted which landing page
    """
    # ToDo: replace ForeignKey with Generic Foreign Key if applicable
    server = models.ForeignKey(
        OutlineServer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    url = models.TextField()

    date = models.DateField(
        null=True,
        blank=True)


class RequestStatus(models.TextChoices):
    """
    Request status choices
    """

    ACCEPTED = '1', 'ACCEPTED'
    INVLAID = '2', 'INVALID'


class RequestSource(models.IntegerChoices):
    """
    Request source choices
    """

    BEEPASS = 1, 'BEEPASS VPN'
    BEEPASS_X = 2, 'BEEPASS VPN X'


class FailureCause(models.TextChoices):
    """
    Cause of failure choices
    """

    NA = '0', 'Not Applicable'
    REQUESTED_SERVERS_NOT_FOUND = '1', 'Requested servers not found or off'
    CHECK_SERVERS_OFF = '2', 'CHECK_FOR_SERVERS Setting is set to False'
    NO_CAMPAIGNS = '3', 'No Campaigns found'


class RequestsHistory(models.Model):
    """
    List of invalid and accepted requests
    """

    status = models.CharField(
        max_length=2,
        db_index=True,
        choices=RequestStatus.choices,
        default=RequestStatus.INVLAID)

    source = models.IntegerField(
        db_index=True,
        choices=RequestSource.choices,
        default=RequestSource.BEEPASS)

    ip_address = models.CharField(
        max_length=256,
        null=True,
        blank=True)

    ip_address_fwd = models.CharField(
        max_length=256,
        null=True,
        blank=True)

    user_agent = models.TextField(
        blank=True,
        null=True)

    created = models.DateTimeField(
        blank=False,
        null=True,
        default=timezone.now,
        verbose_name='created')

    timestamp = models.DateTimeField(
        auto_now=True)

    method = models.CharField(
        max_length=1000)

    headers = models.JSONField(
        default=dict)

    path = models.CharField(
        max_length=1000)

    uri = models.CharField(
        max_length=2000)

    host = models.CharField(
        max_length=1000)

    meta = models.TextField(
        null=True,
        blank=True)

    cookies = models.TextField(
        blank=True,
        null=True)

    is_secure = models.BooleanField()

    is_ajax = models.BooleanField()

    # For invalid requests
    # accepted requests will get 'NA' as their cause of failure
    failure_cause = models.CharField(
        max_length=2,
        choices=FailureCause.choices,
        default=FailureCause.NA)

    campaign = models.ForeignKey(
        Campaign,
        null=True,
        blank=True,
        db_index=True,
        related_name='requests',
        on_delete=models.SET_NULL)

    ownclient = models.BooleanField(
        default=True)

    ownserver = models.BooleanField(
        default=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        impression_counter.labels(
            status=self.status,
            campaign=self.campaign.name if self.campaign else 'NA').inc()

    class Meta:
        verbose_name_plural = 'Requests History'


class RequestsHistoryAggregate(models.Model):
    """
    A model to define aggregate requests history records
    """

    source = models.IntegerField(
        db_index=True,
        choices=RequestSource.choices,
        default=RequestSource.BEEPASS)

    status = models.CharField(
        max_length=2,
        choices=RequestStatus.choices,
        default=RequestStatus.INVLAID)

    campaign = models.ForeignKey(
        Campaign,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='hourly_requests')

    timestamp = models.DateTimeField()

    count = models.IntegerField(
        default=0)

    class Meta:
        verbose_name_plural = 'Requests History Aggregate'

        constraints = [
            models.UniqueConstraint(fields=['status', 'campaign', 'timestamp', 'source'], name='unique_aggregate')
        ]
