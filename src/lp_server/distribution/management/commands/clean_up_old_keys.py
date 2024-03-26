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

from distribution.models import OutlineUser, Vpnuser
from distribution.serializers import OutlineuserSerializer
from django.core.management.base import BaseCommand

from distribution.utils import get_key_dict


class Command(BaseCommand):
    help = 'Clean up old active keys and keep one active key for each user'

    def handle(self, *args, **options):

        latest_active_keys = []
        for user in Vpnuser.objects.all():
            try:
                latest_active_key = user.outline_keys.filter(active=True, exists_on_server=True, removed=False).latest('updated_date')
                latest_active_keys.append(latest_active_key.id)
            except OutlineUser.DoesNotExist:
                continue

        old_keys = OutlineUser.objects.filter(active=True).exclude(id__in=latest_active_keys)
        count = old_keys.count()

        self.stdout.write(self.style.SUCCESS(
            f'Found {count} active keys to be deleted'))

        # Populate a list of to be deleted key dicts
        key_list = get_key_dict(old_keys)

        failed_keys = []
        try:
            failed_keys = OutlineuserSerializer.remove_key_from_server(key_list)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                f'Deleting keys failed due to {str(exc)}'))
            return

        deleted_keys = [key for key in old_keys if key.id not in failed_keys]
        deleted_count = len(deleted_keys)

        self.stdout.write(self.style.SUCCESS(
            f'Removing {deleted_count} keys from the db'))

        OutlineuserSerializer.remove_keys_from_db(deleted_keys)

        deleted_keys_ids = [key.id for key in deleted_keys]

        inactive_keys = OutlineUser.objects.filter(id__in=deleted_keys_ids).update(active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Deactivated {inactive_keys} keys'))

        active_keys_count = len(latest_active_keys)

        self.stdout.write(self.style.SUCCESS(
            f'Deleted {inactive_keys} out of {count} keys. There is currently {active_keys_count} active keys.'))
