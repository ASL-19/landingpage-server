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

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from solo.models import SingletonModel

from ckeditor_uploader.fields import RichTextUploadingField

from notification.utils import send_telegram, send_email
from lp_server.models import DatedMixin
from distribution.models import Vpnuser

logger = logging.getLogger(__name__)


def get_deadline():
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today + settings.EXPIRATION_NOTIFICATION_MESSAGE


class ParserType(models.TextChoices):
    TEXT = 'TEXT', _('TEXT')
    HTML = 'HTML', _('HTML')
    MARKDOWN = 'MARKDOWN', _('MARKDOWN')


class MessageStatus(models.TextChoices):
    PENDING = 'PENDING', _('PENDING')
    SCHEDULED = 'SCHEDULED', _('SCHEDULED')
    SENT = 'SENT', _('SENT')
    OPTEDOUT = 'OPTEDOUT', _('OPTED OUT')
    FAILED = 'FAILED', _('FAILED')


class NotificationMessage(DatedMixin):
    """
    Model definition for notification messages
    """

    broadcast = models.ForeignKey(
        'NotificationBroadcast',
        on_delete=models.CASCADE,
        related_name='messages')

    user = models.ForeignKey(
        Vpnuser,
        on_delete=models.CASCADE,
        related_name='notifications')

    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING,
        editable=False)

    attempts = models.IntegerField(
        _('Number of attempts'),
        default=0)

    sent = models.DateTimeField(
        _('Sent on'),
        null=True,
        blank=True)

    error_msg = models.TextField(
        default='N/A')

    def send(self, text, subject=None):
        """
        Send a notification message to a user

        :param text: Text to be sent to the user
        :return: Number of notifications sent
        """

        if self.user.channel == 'TG':
            if self.user.userchat and self.user.userchat != '0':
                try:
                    msg = text.replace('<br />', '')
                    return send_telegram(
                        self.user,
                        self.user.userchat,
                        msg,
                        keyboard=[],
                        parse=None if self.broadcast.parser_type == ParserType.TEXT else self.broadcast.parser_type)
                except Exception as exc:
                    logger.error(
                        f'Unable to send telegram message to {self.user.id} ({str(exc)})')
                    raise
        elif self.user.channel == 'EM':
            if self.user.userchat and self.user.userchat != '0':
                try:
                    return send_email(subject, self.user.username, text)
                except Exception as exc:
                    logger.error(
                        f'Unable to sending email to {self.user.id} ({str(exc)})')
                    raise
        elif self.user.channel == 'SG':
            # TODO: Add sending functionality for Signal
            raise Exception(f'Sending to users on the {self.user.channel} channel is not yet supported.')
        else:
            raise Exception(f'User {self.user.username} does not have a channel')

    def __str__(self):
        return f'{self.status} for {self.user.username} via {self.user.channel} channel'

    class Meta:
        db_table = 'distribution_notificationmessage'
        verbose_name = 'Notification Message'
        verbose_name_plural = 'Notifications Messages'


class BroadcastStatus(models.TextChoices):
    PENDING = 'PENDING', _('PENDING')
    SCHEDULED = 'SCHEDULED', _('SCHEDULED')
    SENT = 'SENT', _('SENT')
    INCOMPLETE = 'INCOMPLETE', _('INCOMPLETE')
    INPROGRESS = 'INPROGRESS', _('IN PROGRESS')
    FAILED = 'FAILED', _('FAILED')


class BroadcastAction(models.TextChoices):
    """
    Broadcast action choices
    """

    NOTIFY = 'NOTIFY', _('Notify VPN users')
    DEACTIVATE = 'DEACTIVATE', _('Deactivate keys')


class NotificationBroadcast(DatedMixin):
    """
    Model definition for broadcasts
    """

    purpose = models.CharField(
        max_length=75,
        null=False,
        blank=False,
        help_text='Used for differentiating '
        'between broadcasts (e.g. Testing TG '
        'notifications internally)')

    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=BroadcastStatus.choices,
        default=BroadcastStatus.PENDING,
        editable=False)

    subject = models.CharField(
        max_length=75)

    body = RichTextUploadingField()

    parser_type = models.CharField(
        _('Body Type'),
        max_length=8,
        choices=ParserType.choices,
        default=ParserType.HTML)

    deadline = models.DateTimeField(
        _('Deadline'),
        null=False,
        blank=False,
        default=get_deadline)

    recipients = models.ManyToManyField(
        Vpnuser,
        through=NotificationMessage)

    scheduled = models.DateTimeField(
        _('Scheduled on'),
        null=True,
        blank=True)

    action = models.CharField(
        _('Action'),
        max_length=10,
        choices=BroadcastAction.choices,
        default=BroadcastAction.NOTIFY)

    def __str__(self):
        return f'{self.status} with subject: {self.subject}'

    def save(self, *args, **kwargs):
        """
        Schedule the broadcast and its messages on save
        """

        if ((self.body != '' or len(self.body) > 0) and
                (self.status in [BroadcastStatus.PENDING, BroadcastStatus.INPROGRESS])):
            now = timezone.now()

            # Update the pending messages of the broadcast
            NotificationMessage.objects \
                .filter(broadcast=self, status=MessageStatus.PENDING) \
                .update(
                    status=MessageStatus.SCHEDULED,
                    updated_date=now)

            # Update the broadcast
            self.status = BroadcastStatus.SCHEDULED
            self.scheduled = now
            self.updated_date = now

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'distribution_notificationbroadcast'
        verbose_name = 'Notification Broadcast'
        verbose_name_plural = 'Notifications Broadcasts'


class NotificationBroadcastConfiguration(SingletonModel):
    """
    Singleton model to set notification broadcast configuration. Eg: purpose of the broadcast, body and subject for the notification message/email
    """
    bc_purpose = models.CharField(
        _('Broadcast purpose'),
        max_length=75,
        null=False,
        blank=False,
        help_text='Used for differentiating '
        'between broadcasts (e.g. Testing TG '
        'notifications internally)')

    notification_subject = models.CharField(
        max_length=75)

    notification_body = RichTextUploadingField()

    parser_type = models.CharField(
        _('Body Type'),
        max_length=8,
        choices=ParserType.choices,
        default=ParserType.HTML)

    def __str__(self):
        return "Notification Broadcast Configuration"

    class Meta:
        verbose_name = "Notification Broadcast Configuration"
