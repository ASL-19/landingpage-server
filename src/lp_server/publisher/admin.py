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

import logging

from django.contrib import admin
from django.db.models import Sum
from django.template.defaultfilters import truncatechars
from rangefilter.filters import DateRangeFilter

from .models import (Campaign, CampaignConsumptionHistory,
                     CampaignFundingHistory, Impression, Region)

logger = logging.getLogger(__name__)


class RunningCampaignsFilter(admin.SimpleListFilter):

    title = 'Running status'
    parameter_name = 'running'

    def lookups(self, request, model_admin):
        return (
            ('on', 'Running'),
            ('off', 'Not running'))

    def queryset(self, request, queryset):
        if self.value() == 'on':
            return queryset.filter(
                approved=True, enabled=True, draft=False, removed=False)
        if self.value() == 'off':
            return queryset.filter(approved=False)


class CampaignAdmin(admin.ModelAdmin):

    list_display = (
        'unique_id',
        'get_organization_name',
        'plan_type',
        'initial_date',
        'start_date',
        'end_date',
        'truncated_url',
        'approved',
        'enabled',
        'draft',
        'removed',
        'internal',
        'impression_per_period',
        'delivered_impressions'
    )

    search_fields = (
        'unique_id',
    )

    list_editable = (
        'approved',
        'enabled',
        'draft',
        'removed',
        'internal',
    )

    list_filter = (
        RunningCampaignsFilter,
        'internal',
        'organization',
        'plan_type',
    )

    readonly_fields = (
        'delivered_impressions',
    )

    save_as = True

    def delivered_impressions(self, obj):
        sum = 0
        if obj:
            sum = Impression.objects.filter(campaign=obj).aggregate(Sum('actual'))['actual__sum']
        return sum if sum else 0

    @admin.display(description='Target URL')
    def truncated_url(self, obj):
        return truncatechars(obj.target_url, 50)

    def get_queryset(self, request):
        qs = super(CampaignAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            org = request.user.organization
            return qs.filter(organization=org)
        except Exception as exc:
            logger.error(f'Filtering queryset failed {str(exc)} ({type(exc)})')
            return qs.none()


class CampaignFundingHistoryAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CampaignConsumptionHistoryAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ImpressionAdmin(admin.ModelAdmin):

    list_display = (
        'campaign',
        'date',
        'actual',
        'desired',
        'percentage',
    )

    list_filter = (
        'campaign__unique_id',
        'date',
        ('date', DateRangeFilter)
    )


admin.site.register(Region)
admin.site.register(Impression, ImpressionAdmin)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(CampaignFundingHistory, CampaignFundingHistoryAdmin)
admin.site.register(CampaignConsumptionHistory, CampaignConsumptionHistoryAdmin)
