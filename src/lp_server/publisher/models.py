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

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from bleach import clean
from django_bleach.utils import get_bleach_default_options

from lp_server.helpers import (
    validate_unique_id_strict, validate_url)

from accounts.models import Organization
from preference.models import Region
from publisher.signals import update_percentage


class BleachCharField(models.CharField):
    """
    Bleach Char Field
    """
    def __init__(self, allowed_tags=None, allowed_attributes=None,
                 allowed_styles=None, allowed_protocols=None,
                 strip_tags=None, strip_comments=None, *args, **kwargs):

        super(BleachCharField, self).__init__(*args, **kwargs)

        self.bleach_kwargs = get_bleach_default_options()

        if allowed_tags:
            self.bleach_kwargs['tags'] = allowed_tags
        if allowed_attributes:
            self.bleach_kwargs['attributes'] = allowed_attributes
        if allowed_styles:
            self.bleach_kwargs['styles'] = allowed_styles
        if allowed_protocols:
            self.bleach_kwargs['protocols'] = allowed_protocols
        if strip_tags:
            self.bleach_kwargs['strip'] = strip_tags
        if strip_comments:
            self.bleach_kwargs['strip_comments'] = strip_comments

    def pre_save(self, model_instance, add):
        data = getattr(model_instance, self.attname)
        if data:
            clean_value = clean(
                data,
                **self.bleach_kwargs
            )
            setattr(model_instance, self.attname, clean_value)
            return clean_value

        return data


class PlanType(models.TextChoices):
    ONETIME = '1', 'ONE-TIME'
    MONTHLY = '2', 'MONTHLY'


class Campaign(models.Model):
    """
    Campaign model
    """

    plan_type = models.CharField(
        max_length=2,
        choices=PlanType.choices,
        default=PlanType.MONTHLY,
        help_text=_('The type of plan, e.g. one-time or monthly'))
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='campaigns',
        null=True,
        blank=False)
    unique_id = models.CharField(
        max_length=64,
        validators=[validate_unique_id_strict],
        help_text=_('The unique id by which the campaign can be identified by the partner'))
    name = BleachCharField(
        max_length=255,
        help_text=_('The name of the campaign'))
    impression_per_period = models.IntegerField(
        default=0,
        help_text=_('the number of impressions to be served during the period'))
    initial_date = models.DateTimeField(
        default=datetime.datetime.fromtimestamp(0),
        help_text=_('initial start date of the campaign'))
    start_date = models.DateTimeField(
        help_text=_('start date of the campaign (changes each month for monthly plans)'))
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('end date of the campaign'))
    target_url = BleachCharField(
        max_length=1024,
        verbose_name=_('target url'),
        null=True,
        blank=True,
        validators=[validate_url])
    has_website = models.BooleanField(
        default=True,
        help_text=_('Whether or not the campaign creator needs a new website for the campaign'))
    source = BleachCharField(
        max_length=32,
        null=True,
        blank=True,
        verbose_name=_('campaign source'))
    medium = BleachCharField(
        max_length=32,
        null=True,
        blank=True,
        verbose_name=_('campaign medium'))
    target_regions = models.ManyToManyField(
        Region,
        blank=True)
    approved = models.BooleanField(
        default=False,
        help_text=_('if the campaign is approved by the admin'))
    enabled = models.BooleanField(
        default=True,
        help_text=_('if the campaign is enabled by the creator and on going'))
    draft = models.BooleanField(
        default=False,
        help_text=_('if the campaign is to be saved as a draft by the creator'))
    removed = models.BooleanField(
        default=False,
        help_text=_(
            'whether or not the organization admins have removed the campaign. '
            'Removed campaigns will not be displayed to users'))
    internal = models.BooleanField(
        default=False,
        help_text=_(
            'whether or not the campaign is for an ASL19 project'))

    def __str__(self):
        return self.unique_id

    @property
    def landing_page(self):
        if self.source and self.medium:
            return settings.UTM_URL_TEMPLATE.format(
                url=self.target_url,
                source=self.source,
                name=self.name,
                medium=self.medium)
        return self.target_url

    def get_organization_name(self):
        if self.organization:
            return self.organization.name
        else:
            return None
    get_organization_name.short_description = 'Organization'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization', 'unique_id'], name='unique_organization_id')
        ]


post_save.connect(update_percentage, sender=Campaign)


class CampaignFundingHistory(models.Model):
    """
    Model which stores the record of each payment for each campaign
    """

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text=_('the amount of funding added to the campaign'))
    payment_date = models.DateTimeField(
        help_text=_('the date the payment has gone through'))
    payment_confirmation = models.CharField(
        blank=True,
        max_length=1024,
        help_text=_('Confirmation string received from the payment system'))

    class Meta:
        verbose_name_plural = 'Campaign funding history'


class CampaignConsumptionHistory(models.Model):
    """
    Model which stores the record of each day that campaign has been
    active and the amount it has consumed
    """

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,)
    invoice_id = models.CharField(
        max_length=32,
        help_text=_('The unique id by which the bill can be identified from the partner'))
    consumption_date = models.DateTimeField(
        help_text=_('the day which the consumption corresponds to'))
    number_of_impression = models.IntegerField(
        default=0,
        help_text=_('how many times the campaign has been presented to the user'))
    consumed_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text=_('the amount of funding that has been consumed for the day the campaign'))

    class Meta:
        verbose_name_plural = 'Campaign consumption history'


class Impression(models.Model):
    """
    What is going to be the quota for today based on
    what happened yesterday
    - Publishers
    - Impression
    """

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.PROTECT,
        related_name=_('daily_plans'))
    percentage = models.IntegerField(
        default=0)
    desired = models.BigIntegerField()
    actual = models.BigIntegerField(
        default=0)
    date = models.DateField()

    def update_tomorrow(self):
        tomorrow = self.date + datetime.timedelta(days=1)
        tomorrow_impressions = Impression.objects.filter(campaign=self.campaign.pk, date=tomorrow)
        if tomorrow_impressions.count() == 1:
            tomorrow_impression = tomorrow_impressions.get()
            tomorrow_impression.desired += max(-tomorrow_impression.desired, self.desired - self.actual)
            tomorrow_impression.save()

    def __str__(self):
        return f'{self.campaign.unique_id}:{self.date}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['campaign', 'date'], name='unique_impression_yield')
        ]
