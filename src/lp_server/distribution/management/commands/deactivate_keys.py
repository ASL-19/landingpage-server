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

from distribution.models import OutlineUser, DeletionCause
from distribution.serializers import OutlineuserSerializer
from django.core.management.base import BaseCommand
from django.utils import timezone

from distribution.utils import get_key_dict


class Command(BaseCommand):
    help = 'Deactivate the keys that have a due delete date'

    def add_arguments(self, parser):
        parser.add_argument(
            'days',
            type=int,
            help='Number of days to wait before deleting the inactive key')

    def handle(self, *args, **options):
        days = options['days']

        target_date = timezone.now() - timezone.timedelta(days=days)

        # Update returning keys and remove their delete_date
        # and deletion_cause
        reactivated = OutlineUser.objects.filter(
            delete_date__lte=target_date,
            deletion_cause=DeletionCause.INACTIVE,
            active=True,
            removed=False).update(
                delete_date=None,
                deletion_cause=DeletionCause.NA)

        self.stdout.write(self.style.SUCCESS(
            f'There were {reactivated} reactivated keys whose delete dates were unset.'))

        inactive_keys = OutlineUser.objects.filter(
            delete_date__lte=target_date,
            deletion_cause=DeletionCause.INACTIVE,
            active=False,
            removed=False)

        count = inactive_keys.count()

        # Populate a list of inactive key dicts
        key_list = get_key_dict(inactive_keys)

        failed_keys = []
        try:
            failed_keys = OutlineuserSerializer.remove_key_from_server(key_list)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                f'Deleting keys failed due to {str(exc)}'))
            return

        deleted_keys = [key for key in inactive_keys if key.id not in failed_keys]
        OutlineuserSerializer.remove_keys_from_db(deleted_keys)

        deleted_count = len(deleted_keys)

        self.stdout.write(self.style.SUCCESS(
            f'Deleted {deleted_count} out of {count} keys'))
