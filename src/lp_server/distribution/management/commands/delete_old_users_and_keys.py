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

from distribution.models import Vpnuser, OutlineUser
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Delete users and keys belonging to the old distribution system'

    def add_arguments(self, parser):
        parser.add_argument(
            'batch_size',
            type=int,
            default=100,
            help='Number of users to delete along with their keys')

    def handle(self, *args, **options):
        target = options['batch_size']

        users_pk = Vpnuser.objects.all().order_by('id').values_list('pk')[:target]
        users = Vpnuser.objects.filter(pk__in=users_pk)
        self.stdout.write(self.style.SUCCESS(
            'Deleting {} users and their associated keys'.format(users.count())))
        count = users.count()
        for user in users:
            keys = OutlineUser.objects.filter(user=user)
            try:
                keys.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully deleted keys for user {user}'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f'Error during deleting keys {str(exc)} for user {user}'))
        try:
            users.delete()
            self.stdout.write(self.style.SUCCESS(
                'Successfully deleted {} users'.format(count)))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(
                'Error during deleting users {}'.format(str(exc))))
