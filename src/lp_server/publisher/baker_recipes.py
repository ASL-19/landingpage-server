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

from model_bakery.recipe import (
    Recipe, seq,
)
import datetime
import random

from django.utils import timezone
from django.contrib.auth.models import Group

from accounts.models import User, Organization
from publisher.models import Campaign, PlanType


def organization_get_or_create(**kwargs):
    """
    https://stackoverflow.com/q/39098510
    This is created to replace using model_bakery's foreign_key with recipes
    Returns a closure with details of the organization to be fetched from db or
    created. Must be a closure to ensure it's executed within a test case
    Parameters
    ----------
    kwargs
        the details of the desired organization
    Returns
    -------
    Closure
        which returns the desired organization
    """

    def get_org():
        org, new = Organization.objects.get_or_create(**kwargs)
        return org

    return get_org


great_org = organization_get_or_create(name='Great Organization')
awesome_org = organization_get_or_create(name='Awesome Organization')
amazing_org = organization_get_or_create(name='Amazing Organization')


organization_group = Recipe(
    Group,
    name='organizations'
)


great_user = Recipe(
    User,
    username='great',
    email='great@example.com',
    password='greatpassword',
    organization=great_org,
    role='1',
    is_active=True,
    time_zone='EDT',
    currency='EUR',
    invited=False)
awesome_user = Recipe(
    User,
    username='awesome',
    email='awesome@example.com',
    password='awesomepassword',
    organization=awesome_org,
    role='1',
    is_active=True,
    time_zone='PDT',
    currency='USD',
    invited=False)
amazing_user = Recipe(
    User,
    username='amazing',
    email='amazing@example.com',
    password='amazingpassword',
    organization=amazing_org,
    role='1',
    is_active=True,
    time_zone='CET',
    currency='CAD',
    invited=False)

great_campaign = Recipe(
    Campaign,
    plan_type=PlanType.ONETIME,
    organization=great_org,
    unique_id=seq('great_campaign'),
    name='Great Campaign',
    impression_per_period=random.randint(1000000, 2000000),
    start_date=timezone.now(),
    end_date=timezone.now() + datetime.timedelta(days=30),
    target_url='https://greatorgabization.org/campaign1',
    has_website=True,
    source='asl',
    medium='vpn',
    approved=True,
    enabled=True,
    draft=False,
    removed=False)
awesome_campaign = Recipe(
    Campaign,
    plan_type=PlanType.ONETIME,
    organization=awesome_org,
    unique_id=seq('awesome_campaign'),
    name='Awesome Campaign',
    impression_per_period=random.randint(1000000, 2000000),
    start_date=timezone.now() - datetime.timedelta(days=15),
    end_date=timezone.now() + datetime.timedelta(days=15),
    target_url='https://awesomeorganization.org',
    has_website=True,
    source='asl19',
    medium='aslvpn',
    approved=True,
    enabled=True,
    draft=False,
    removed=False)
amazing_campaign = Recipe(
    Campaign,
    plan_type=PlanType.ONETIME,
    organization=amazing_org,
    unique_id=seq('amazing_campaign'),
    name='Amazing Campaign',
    impression_per_period=random.randint(1000000, 2000000),
    start_date=timezone.now(),
    end_date=timezone.now() + datetime.timedelta(days=60),
    target_url='https://amazingorganization.org',
    has_website=True,
    source='asl',
    medium='vpn-asl19',
    approved=True,
    enabled=True,
    draft=False,
    removed=False)
