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

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from distribution.utils import delete_file_from_s3
from distribution.models import OnlineConfig


class Command(BaseCommand):
    help = 'Delete users and keys belonging to the old distribution system'

    def add_arguments(self, parser):
        parser.add_argument(
            'batch_size',
            type=int,
            default=100,
            help='Number of ssconfig json files (associated with deleted users) to delete from S3 bucket')

    def handle(self, *args, **options):
        target = options['batch_size']

        deleted_files = []
        failed_files = []
        try:
            orphan_files = OnlineConfig.objects.filter(Q(outline_user__user__isnull=True) | Q(outline_user__isnull=True)).order_by('id')[:target]
            for of in orphan_files:
                key = f'{of.file_name}.json'
                try:
                    self.stdout.write(f'Getting metadata of {key}')
                    delete_file_from_s3(
                        settings.S3_SSCONFIG_BUCKET_NAME,
                        key)
                    deleted_files.append(of)
                    of.delete()
                except Exception as e:
                    failed_files.append(of)
                    self.stdout.write(self.style.ERROR((f'Unable to get the metadata (bucket={settings.S3_SSCONFIG_BUCKET_NAME}, key={key}) error ({str(e)})')))
            self.stdout.write(self.style.SUCCESS(f'From total of {len(orphan_files)} orphan ssconf files, {len(deleted_files)} were deleted and {len(failed_files)} failed.'))
            self.stdout.write(self.style.SUCCESS(f'Deleted list: {deleted_files}'))
            self.stdout.write(self.style.ERROR(f'Failed list: {failed_files}'))
        except Exception as e:
            raise e
