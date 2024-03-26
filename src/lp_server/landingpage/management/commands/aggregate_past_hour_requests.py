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

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db.models import Count

from publisher.models import Campaign
from landingpage.models import RequestsHistory, RequestsHistoryAggregate, RequestSource


class Command(BaseCommand):
    help = 'Aggregates past-hour Request History rows into hourly RequestHistoryAggregate row'

    def _aggregate_requests(self, start_time, end_time):
        """
        Aggregate requests between start_time and end_time
        """

        for source in RequestSource.choices:
            source = source[0]
            request_groups = RequestsHistory.objects \
                .using(settings.RO_DB) \
                .filter(created__gte=start_time, created__lt=end_time, source=source) \
                .values('status', 'campaign') \
                .annotate(count=Count('status')) \
                .order_by('status')

            total_count = sum(d.get('count', 0) for d in list(request_groups))
            self.stdout.write(
                f'Found {total_count} RequestsHistory records in the past hour for source {source}.')

            if RequestsHistoryAggregate.objects.using(settings.RO_DB).filter(timestamp=start_time, source=source).count() > 0:
                self.stdout.write(
                    f'The past half-hour ({start_time}) RequestsHistory records have already been aggregated for source {source}!')
                return

            RequestsHistoryAggregate.objects.bulk_create([
                RequestsHistoryAggregate(
                    status=group['status'],
                    source=source,
                    timestamp=start_time,
                    campaign=Campaign.objects.get(id=group['campaign']) if group['campaign'] else None,
                    count=group['count']) for group in request_groups
            ])

            self.stdout.write(
                f'Aggregated {total_count} past half-hour ({start_time}) RequestsHistory records for source {source}!')

    def handle(self, *args, **options):
        now_hour = timezone.now().replace(minute=0, second=0, microsecond=0)
        past_half_hour = now_hour - timedelta(hours=0.5)
        past_hour = now_hour - timedelta(hours=1)
        self._aggregate_requests(past_hour, past_half_hour)
        self._aggregate_requests(past_half_hour, now_hour)
