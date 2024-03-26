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

from django.utils import timezone

from lp_server.constants import Messages

from publisher.models import PlanType


def validate_dates(plan_type, parsed_start_date, end_date, parsed_end_date):
    """
    Validate the start and end dates of a campaign

    Args:
        plan_type (str): Either ONE_TIME (1) or MONTHLY (2)
        parsed_start_date (datetime obj): A parsed version of the start_date string
        end_date (str): A string representation of the start_date
        parsed_end_date (datetime obj): A parsed version of the end_date string

    Returns:
        list: A Messages list containing a dict with the message
            and code of the error or None

    """

    now = timezone.now()

    if end_date is None and plan_type == PlanType.ONETIME:
        return Messages.MISSING_END_DATE
    elif end_date is not None and plan_type == PlanType.MONTHLY:
        return Messages.END_DATE_PROVIDED
    elif parsed_start_date < now:
        return Messages.START_DATE_PRECEDING_TODAY
    elif end_date is not None and parsed_end_date < parsed_start_date:
        return Messages.END_DATE_PRECEDING_START_DATE
    else:
        return None
