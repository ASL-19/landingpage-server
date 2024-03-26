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

import math
import datetime

from django.utils import timezone
from django.db import transaction


@transaction.atomic
def update_percentage(sender, instance, created, **kwargs):
    """
    Updates the percentage of impressions
    """
    from .models import Impression, PlanType

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = max(instance.start_date, today)
    if instance.plan_type == PlanType.ONETIME:
        end_date = instance.end_date
    else:
        end_date = start_date + datetime.timedelta(days=30)
    delta = end_date - start_date + datetime.timedelta(days=1)
    date_list = [start_date + datetime.timedelta(days=x) for x in range(delta.days)]

    if (instance.approved and
            instance.enabled and
            not instance.removed and
            not instance.draft):
        per_day = math.ceil(instance.impression_per_period / delta.days)
    else:
        per_day = 0

    for dt in date_list:
        impression, created = Impression.objects.get_or_create(
            campaign=instance,
            date=dt,
            defaults={
                'desired': per_day
            })
        impression.desired = per_day
        impression.save()

    impressions = Impression.objects.filter(
        date__in=date_list,
    ).order_by('date')

    impdic = {}
    for impression in impressions:
        key = str(impression.date)
        if key in impdic:
            impdic[key]['sum'] += float(impression.desired)
            impdic[key]['impressions'].append(impression)
        else:
            impdic[key] = {
                'sum': float(impression.desired),
                'impressions': [impression, ]
            }

    for key, value in impdic.items():
        sum = value['sum']
        for impression in value['impressions']:
            if sum <= 0:
                impression.percentage = 0
            else:
                impression.percentage = round(100 * float(impression.desired) / sum)
            impression.save()
