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

import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from landingpage.models import RequestsHistory, RequestsHistoryAggregate
from landingpage.utils import aggregate_request_history_log


class Command(BaseCommand):
    help = 'Aggregates Request History rows into hourly RequestHistoryAggregate rows'

    def add_arguments(self, parser):
        parser.add_argument(
            'start_time',
            type=str,
            help='Datetime (format e.g: 2023-01-30T10:00) to start aggregation of requests history')

        parser.add_argument(
            'end_time',
            type=str,
            help='Datetime (format e.g: 2023-01-30T10:00) to stop aggregation of requests history')

    def handle(self, *args, **options):
        aggregated = 0

        # We start from the latest requests down to the oldest
        start_time = datetime.datetime.strptime(options['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.datetime.strptime(options['end_time'], '%Y-%m-%dT%H:%M')

        # Avoid duplication by deleting existing aggregates
        RequestsHistoryAggregate.objects.filter(
            timestamp__gte=start_time,
            timestamp__lt=end_time
        ).delete()

        qs = RequestsHistory.objects.filter(
            created__gte=start_time,
            created__lt=end_time
        ).order_by('-id')
        paginator = Paginator(qs, 2000)
        num_pages = paginator.num_pages

        for page in range(1, num_pages + 1):
            self.stdout.write(f'Page {page} out of {num_pages}')
            for req in paginator.page(page).object_list:
                if req.created.minute >= 30:
                    req_hour = req.created.replace(minute=30, second=0, microsecond=0)
                else:
                    req_hour = req.created.replace(minute=0, second=0, microsecond=0)
                aggregate_request_history_log(req.status, req_hour, req.campaign)
                aggregated += 1

        self.stdout.write(f'Aggregated {aggregated} RequestsHistory records!')
