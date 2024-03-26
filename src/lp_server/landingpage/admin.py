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

from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from .models import (
    LandingPage, RequestsHistory, RequestsHistoryAggregate)


class RequestsHistoryAdmin(admin.ModelAdmin):

    list_display = (
        'status',
        'created',
        'campaign',
        'source',
        'failure_cause',
    )

    list_filter = (
        'source',
        'status',
        'failure_cause',
        'campaign',
        ('created', DateRangeFilter),
    )

    search_fields = ['campaign__name']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class RequestsHistoryAggregateAdmin(admin.ModelAdmin):

    list_display = (
        'status',
        'campaign',
        'source',
        'timestamp',
        'count')

    list_filter = (
        'source',
        'status',
        'campaign',
        ('timestamp', DateRangeFilter))

    ordering = ('-timestamp',)

    search_fields = ['campaign__name']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class LandingPageAdmin(admin.ModelAdmin):

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(LandingPage, LandingPageAdmin)
admin.site.register(RequestsHistory, RequestsHistoryAdmin)
admin.site.register(RequestsHistoryAggregate, RequestsHistoryAggregateAdmin)
