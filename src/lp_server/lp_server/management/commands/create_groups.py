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

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create/update user groups required for the distribution app'

    def handle(self, *args, **options):
        for index, (group_name, group) in enumerate(settings.PREDEFINED_GROUPS.items()):
            self.stdout.write(f'Create/update the permissions of `{group_name}`')
            try:
                grp = Group.objects.get(name=group_name)
                Group.objects.get(name=group_name)
                self.stdout.write(f'\t{group_name} already exists!')
            except Group.DoesNotExist:
                grp = Group.objects.create(name=group_name)

            # Clear all the existing permissions of each group
            # to allow for an exact match with the JSON of
            # the PREDEFINED_GROUPS setting in case of any permission change
            self.stdout.write(f'Clearing all the existing permissions of `{group_name}`')
            grp.permissions.clear()

            for obj in group:
                for permission in obj['permissions']:
                    name = f"Can {permission} {obj['model']}"
                    self.stdout.write(f'\tAdding `{name}`')
                    try:
                        model_add_perm = Permission.objects.get(name=name)
                    except Permission.DoesNotExist:
                        self.stderr.write(f'Permission not found with name ({name}).')
                        continue
                    grp.permissions.add(model_add_perm)
            grp.save()
