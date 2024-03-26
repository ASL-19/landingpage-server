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

from distribution.models import OutlineUser
from distribution.serializers import OutlineuserSerializer
from django.core.management.base import BaseCommand

from distribution.utils import get_key_dict


class Command(BaseCommand):
    help = 'Delete keys that were not removed from servers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            nargs='?',
            help='Max number of keys to remove - to limit the runtime - Default = 100, -1 for unlimited number')
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Print verbose messages')

    def handle(self, *args, **options):
        count = options['count']
        verbose = options['verbose']
        if count == -1:
            keys = OutlineUser.objects.filter(exists_on_server=True, removed=True)
        else:
            keys = OutlineUser.objects.filter(exists_on_server=True, removed=True)[:count]
        total = keys.count()
        self.stdout.write(self.style.SUCCESS(f'{total} keys to remove'))
        if total > 0:
            removed = 0
            for key in keys:
                key_list = get_key_dict([key])
                failed = OutlineuserSerializer.remove_key_from_server(key_list)
                if failed:
                    self.stdout.write(self.style.WARNING(f'Failed to remove key {key.id}'))
                else:
                    if verbose:
                        self.stdout.write(f'Removed key {key.id}')
                    removed += 1

                if removed % 100 == 0:
                    self.stdout.write(self.style.SUCCESS(f'{removed} from {total} keys has been removed'))

            self.stdout.write(self.style.SUCCESS(f'{removed} of {total} keys have been removed'))
