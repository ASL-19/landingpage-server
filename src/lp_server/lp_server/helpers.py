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

import re
import datetime
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

strict_unique_id_regex = re.compile(r'^[a-z\d][a-z\d-]*[a-z\d]$')


def validate_unique_id_strict(value):
    if not strict_unique_id_regex.match(value):
        raise ValidationError(
            _("'%(value)s' can only contain lower-case a-z, digits, and '-' (hyphen), and must not begin or end with '-'"),
            params={'value': value})


def validate_url(url):
    validator = URLValidator(schemes=['https'])  # Only 'https' URLs are accepted

    try:
        validator(url)
    except ValidationError:
        raise ValidationError(_("Please enter a valid URL that starts with 'https://'"), code='invalid_url')


def to_utc_datetime(s):
    """
    Converts an ISO 8601 datetime string into a python datetime object

    Args:
        s (str): An ISO 8601 string, e.g. 2021-01-22T20:40:00+00:00

    Returns:
        datetime obj: A UTC localized datetime object
    """
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')


def to_user_datetime(s, time_zone):
    """
    Converts an ISO 8601 datetime string into a python datetime object

    Args:
        s (str): date of format YYYY-MM-DD, e.g. 2021-01-22
        time_zone (pytz.timezone): user timezone

    Returns:
        datetime obj: A localized (user timezone) datetime object
    """
    date = datetime.datetime.strptime(s, '%Y-%m-%d')
    return time_zone.localize(date)
