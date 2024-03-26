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

from distribution.models import Vpnuser
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Reset users reputation'

    def add_arguments(self, parser):
        parser.add_argument(
            'max_reputation',
            type=int,
            help='Reset users with reputation greater than max_reputation')

    def handle(self, *args, **options):
        max_rep = options['max_reputation']
        if max_rep is None:
            self.stderr.write(self.style.ERROR(
                'Please indicate max-reputation value'))
            return -1

        users = Vpnuser.objects.filter(reputation__gt=max_rep)
        users_count = users.update(reputation=0)
        self.stdout.write(self.style.SUCCESS(
            f'Updated {users_count} users\' reputation back to 0'))
