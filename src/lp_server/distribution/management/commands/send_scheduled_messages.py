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
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from distribution.models import OutlineUser, DeletionCause, NotificationStatus
from notification.models import (
    NotificationBroadcast, BroadcastStatus,
    MessageStatus, BroadcastAction)


class Command(BaseCommand):
    help = 'Send scheduled messages to telegram and/or email users'

    def add_arguments(self, parser):
        parser.add_argument(
            'limit',
            type=int,
            help='How many messages we send to users per second')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Does not send the scheduled messages to the users, it just runs a simulation to test the flow.')

    def handle(self, *args, **options):  # noqa: C901
        limit = options['limit']
        dry_run = options['dry_run']

        # Check for any expired broadcasts and mark them as INCOMPLETE
        expired = NotificationBroadcast.objects.filter(
            status=BroadcastStatus.SCHEDULED,
            deadline__lte=timezone.now())

        if not dry_run:
            if expired.count() > 0:
                for bc in expired:
                    bc.status = BroadcastStatus.INCOMPLETE
                    bc.save()

        try:
            earliest_bc = NotificationBroadcast.objects.filter(
                status=BroadcastStatus.SCHEDULED,
                deadline__gt=timezone.now()) \
                .earliest('created_date')
        except NotificationBroadcast.DoesNotExist:
            # Exit
            self.stdout.write(
                'There are no scheduled broadcasts to be sent at this time.')
            return

        self.stdout.write(
            f'Broadcast "{earliest_bc}" is the first in queue!')

        # filtering messages with associated user having `notification_status=Enabled`
        scheduled_msgs = earliest_bc.messages.filter(
            user__notification_status=NotificationStatus.ENABLED,
            status__in=[
                MessageStatus.SCHEDULED,
                MessageStatus.FAILED]) \
            .order_by('updated_date')[:settings.NOTIFICATION_MAX_JOB_BATCH_LIMIT]

        deactivate_on = True if earliest_bc.action == BroadcastAction.DEACTIVATE else False

        count = scheduled_msgs.count()
        if count > 0:
            self.stdout.write(
                f'"{count}" scheduled messages are to be sent in this job.')
        else:
            # Exit
            self.stdout.write(
                'There are no scheduled messages to be sent at this time.')
            return

        sent_count = failed_count = optedout_count = run_count = 0
        # Limits
        # TG: 30 users/sec
        # EM: 50 emails/sec
        # Used rate: 15 users/sec => 900 users/min => 54K users/hour
        for i, msg in enumerate(scheduled_msgs, start=1):
            start_time = time.time()

            run_count += 1

            if dry_run:
                self.stdout.write(
                    f'[Dry Run] [{timezone.now()}] The message "{msg.id}" will NOT be sent to the user.')

            if msg.user.userchat and msg.user.userchat != '0':

                # Check for max attempts
                if msg.attempts >= settings.NOTIFICATION_MAX_ATTEMPTS_LIMIT:
                    if 'ATTEMPTS MAXED OUT' not in msg.error_msg:
                        msg.error_msg = msg.error_msg + '\nATTEMPTS MAXED OUT!'
                    # Increment the failed counter
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(
                        f'\tAllowed attempts for "{msg}" are maxed out! It will NOT be sent out.'))

                    msg.attempts += 1

                    if not dry_run:
                        msg.save()

                    # Skip ahead
                    continue

                try:
                    # Do NOT send the notification if it is a dry run
                    if not dry_run:
                        msg.send(earliest_bc.body, earliest_bc.subject)

                    msg.sent = timezone.now()
                    msg.status = MessageStatus.SENT

                    # Increment the sent counter
                    sent_count += 1
                except Exception as exc:
                    msg.status = MessageStatus.FAILED
                    msg.error_msg = str(exc)

                    # Increment the failed counter
                    failed_count += 1

                    self.stdout.write(self.style.ERROR(
                        f'\tSending the message "{msg}" failed: {exc}'))
            else:
                # Mark users who haven't agreed yet
                # to receive notifications
                # or rejected the notifications as OPTED OUT
                msg.status = MessageStatus.OPTEDOUT

                optedout_count += 1

            msg.attempts += 1  # Increase attempts after attempting to send

            # Save the message changes
            if not dry_run:
                msg.save()

            # Protect against overflowing the Telegram and/or SES servers
            # Exit if we discover that we are overflowing over the threshold
            if not i % limit:  # if remainder is 0
                if dry_run:
                    self.stdout.write(f'Sent {run_count} out of {limit} messages in last limit run.')

                if run_count > settings.NOTIFICATION_THRESHOLD_PER_SECOND:
                    self.stdout.write(
                        f'S: {sent_count} | F: {failed_count} | O: {optedout_count} | Total: {count}')

                    # Mark the current broadcast as SCHEDULED from IN PROGRESS
                    # before we exit to consider resending the remaining msgs
                    # in the next send-outs
                    if not dry_run:
                        earliest_bc.status = BroadcastStatus.SCHEDULED
                        earliest_bc.save()

                    # Exit process
                    self.stderr.write(
                        'Notification threshold per second has been passed! Exiting process...')
                    return
                run_count = 0

            # Sleep to enforce the rate of {limit} messages/second
            time.sleep(max(1.0 / limit - (time.time() - start_time), 0))

        # filtering counts, messages with only associated user having `notification_status=NotificationStatus.ENABLED`
        if not dry_run:
            total = earliest_bc.messages.filter(user__notification_status=NotificationStatus.ENABLED).count()
            total_sent = earliest_bc.messages.filter(
                user__notification_status=NotificationStatus.ENABLED,
                status__in=[MessageStatus.SENT, MessageStatus.OPTEDOUT]).count()
            total_failed = earliest_bc.messages.filter(
                user__notification_status=NotificationStatus.ENABLED,
                status=MessageStatus.FAILED,
                attempts__gt=settings.NOTIFICATION_MAX_ATTEMPTS_LIMIT).count()

            # Mark the current broadcast as:
            # SENT, if all the messages are either sent or opted-out
            # FAILED, if there is at least one failed message that maxed-out the attempts limit
            # else SCHEDULED
            if total == total_sent:
                earliest_bc.status = BroadcastStatus.SENT
            elif total_failed > 0:
                earliest_bc.status = BroadcastStatus.FAILED
            else:
                earliest_bc.status = BroadcastStatus.SCHEDULED

            earliest_bc.save()

            if deactivate_on:
                # Set the inactive keys of the current recipients for deletion
                # after settings.EXPIRATION_OUTLINE_KEY period
                if earliest_bc.status in [BroadcastStatus.SENT, BroadcastStatus.FAILED]:
                    self.stdout.write('Deactivate action detected!')
                    OutlineUser.objects.filter(
                        user__id__in=earliest_bc.messages.values_list('user_id', flat=True),
                        active=False,
                        removed=False).update(
                            deletion_cause=DeletionCause.INACTIVE,
                            delete_date=timezone.now() + settings.EXPIRATION_OUTLINE_KEY)

        if sent_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\nSuccessfully sent "{sent_count}" out of the "{count}" scheduled messages!'))

        if failed_count > 0:
            self.stdout.write(self.style.ERROR(
                f'\nFailed to send "{failed_count}" scheduled messages due to errors.'))

        if optedout_count > 0:
            self.stdout.write(self.style.WARNING(
                f'\n"{optedout_count}" out of "{count}" scheduled messages were not sent to opted-out users.'))
