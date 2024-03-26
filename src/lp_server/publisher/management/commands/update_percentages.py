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
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from publisher.models import (
    Campaign,
    PlanType)


class Command(BaseCommand):
    help = 'Renew active and approved monthly campaigns that are expiring today.'

    def handle(self, *args, **options):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        amonth = today + relativedelta(months=1)

        expiring_campaigns = Campaign.objects.filter(  # Campaigns that are about to expire
            end_date__lt=today,
            approved=True,
            enabled=True,
            draft=False,
            removed=False,
            plan_type=PlanType.MONTHLY)

        new_campaigns = Campaign.objects.filter(  # Campaigns that are about to begin
            start_date__lt=today,
            end_date__isnull=True,
            approved=True,
            enabled=True,
            draft=False,
            removed=False,
            plan_type=PlanType.MONTHLY)

        campaigns = expiring_campaigns.union(new_campaigns)

        self.stdout.write(f'Found {campaigns.count()} campaigns')
        for campaign in campaigns:
            campaign.start_date = today
            campaign.end_date = amonth
            campaign.save()
            self.stdout.write(f'Campaign {campaign.name} is updated.')
