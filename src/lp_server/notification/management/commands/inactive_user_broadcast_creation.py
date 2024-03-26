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

from django.core.management.base import BaseCommand
from django.utils import timezone

from distribution.models import OutlineUser
from notification.models import NotificationBroadcast, NotificationBroadcastConfiguration, BroadcastAction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Notify inactive users from system and send an email to them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Does not update the users, just prints the counts that would be run.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        inactive_users = OutlineUser.objects.filter(active=False, removed=False).values_list('user', flat=True)

        if dry_run:
            self.stdout.write(f'[Dry Run] [{timezone.now()}]: {len(inactive_users)} Users to be added into Notification Broadcast with Deactivate action!')

        try:
            notification_broadcast_config = NotificationBroadcastConfiguration.objects.get()
        except NotificationBroadcastConfiguration.DoesNotExist:
            self.stdout.write(f'Notification Broadcast configuration does not exists!')
            return

        # if notification broadcast configuration object is not set
        if not notification_broadcast_config.bc_purpose or not notification_broadcast_config.notification_subject or not notification_broadcast_config.notification_body:
            self.stdout.write(f'Notification Broadcast configuration does not exists!')
            return

        # Creating a new pending notification broadcast with DEACTIVATE action
        if not dry_run:
            broadcast = NotificationBroadcast.objects.create(purpose=notification_broadcast_config.bc_purpose, action=BroadcastAction.DEACTIVATE)

            logger.info('Adding recipients ...')
            broadcast.recipients.add(*inactive_users)
            logger.info('All recipients were added!')

            # udpating broadcast subject, body and type
            broadcast.subject = notification_broadcast_config.notification_subject
            broadcast.body = notification_broadcast_config.notification_body
            broadcast.parser_type == notification_broadcast_config.parser_type
            broadcast.save()
            logger.info('Updated Notification Broadcast subject, body and type!')
        else:
            self.stdout.write(f'[Dry Run] [{timezone.now()}]: Creating new Notification Broadcast ...')
            self.stdout.write(f'[Dry Run] [{timezone.now()}]: Updated Notification Broadcast subject, body and type!')
            return
