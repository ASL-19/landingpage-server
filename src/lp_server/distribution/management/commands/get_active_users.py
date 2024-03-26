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

# import operator
# from functools import reduce
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.db.models import Q
from django.utils import timezone

from distribution.models import OutlineUser, DeletionCause


class Command(BaseCommand):
    help = 'Retrieve active users from monitoring system and mark them active in the db'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Does not update the users, just prints the counts that would be run.',
        )

    def _get_active_users(self):
        query = f"""
                SELECT
                    ip, access_key
                FROM
                    ssdbytes
                WHERE
                    time > NOW()-INTERVAL '{settings.PURGE_INACTIVE_NOTIFY}d'
                """
        with connections['prometheus'].cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        return rows

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        users = self._get_active_users()
        self.stdout.write(f'Found {len(users)} Active Users, updating...')
        last_date = timezone.now() - timedelta(days=settings.PURGE_INACTIVE_NOTIFY)
        active_users = []

        for user in users:
            # Any user who doesn't have a server in the list is inactive.
            # user[0] is user's key_id which is unique on each server
            # user[1] is user's server IP:Port
            try:
                outline_user = OutlineUser.objects.filter(Q(server__ipv4=user[0].split(':')[0], outline_key_id=user[1])).first()
            except OutlineUser.DoesNotExist:
                self.stderr.write(f'OutlineUser for {user} was not found')
                continue
            except OutlineUser.MultipleObjectsReturned:
                self.stderr.write(f'Error: Multiple OutlineUsers for {user} were found')
                continue
            except ValueError:
                self.stderr.write(f'Error: Invalid IP address for {user}')
                continue
            if outline_user:
                active_users.append(outline_user.id)

        # Update statistics - We decided to update this value manually
        # stat = Statistics.objects.get(pk=1)
        # stat.active_monthly_users = len(active_users)
        # stat.save()

        self.stdout.write(f'Matched {len(active_users)} users in the DB')
        with transaction.atomic():
            actives = OutlineUser.objects.filter(id__in=active_users).update(active=True)
            inactives = (
                OutlineUser
                .objects
                .filter(created_date__lt=last_date)
                .exclude(id__in=active_users)
                .distinct()
                .update(
                    active=False,
                    delete_date=timezone.now(),
                    deletion_cause=DeletionCause.INACTIVE))
            if dry_run:
                self.stdout.write('Dry running, no value is updated')
                transaction.set_rollback(True)

        self.stdout.write(f'Updated: {actives} active users, {inactives} inactive users')
