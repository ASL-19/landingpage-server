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

from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import SafeText
from django.utils.translation import ngettext
from solo.admin import SingletonModelAdmin

from rangefilter.filters import DateRangeFilter

from notification.models import (
    NotificationMessage,
    NotificationBroadcast,
    MessageStatus,
    NotificationBroadcastConfiguration,
    BroadcastStatus)


class NotificationMessageAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    list_display = (
        'status',
        'vpnuser_link',
        'broadcast_link',
        'attempts',
        'sent',
        'created_date',
        'error_msg')

    list_filter = (
        'broadcast__status',
        'user__channel',
        'status',
        'sent',
        'created_date')

    readonly_fields = (
        'user',
        'status',
        'sent',
        'created_date',
        'updated_date',
        'vpnuser_link',
        'broadcast_link')

    list_per_page = 20
    list_max_show_all = 100
    search_fields = ['user__username']

    def vpnuser_link(self, obj):
        url = resolve_url(admin_urlname(obj.user._meta, SafeText('change')), obj.user.pk)
        return format_html('<a href="{}">{}</a>', url, f'{obj.user.channel}: {obj.user.username}')
    vpnuser_link.short_description = 'User Link'

    def broadcast_link(self, obj):
        url = resolve_url(admin_urlname(obj.broadcast._meta, SafeText('change')), obj.broadcast.pk)
        return format_html('<a href="{}">{}</a>', url, obj.broadcast.purpose)
    broadcast_link.short_description = 'Broadcast Link'


class UnexpiredBroadcastFilter(admin.SimpleListFilter):

    title = 'Expired status'
    parameter_name = 'broadcasts'

    def lookups(self, request, model_admin):
        return (
            ('not_expired', 'Not expired'),
            ('expired', 'Expired'))

    def queryset(self, request, queryset):
        if self.value() == "not_expired":
            return queryset.filter(deadline__gt=timezone.now())
        if self.value() == "expired":
            return queryset.filter(deadline__lte=timezone.now())


class NotificationBroadcastAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    list_display = (
        'status',
        'purpose',
        'subject',
        'messages_link',
        'num_sent',
        'num_failed',
        'num_optedout',
        'updated_date',
        'deadline')

    list_filter = (
        'status',
        UnexpiredBroadcastFilter,
        'parser_type',
        'scheduled',
        'updated_date',
        'action',
        ('created_date', DateRangeFilter),
        ('deadline', DateRangeFilter))

    list_per_page = 10
    list_max_show_all = 100
    search_fields = ['status', 'subject', 'body']

    fields = (
        'status',
        'num_sent',
        'num_failed',
        'num_optedout',
        'action',
        'purpose',
        'subject',
        'body',
        'parser_type',
        'messages_link',
        'scheduled',
        'created_date',
        'updated_date')

    readonly_fields = (
        'status',
        'scheduled',
        'created_date',
        'updated_date',
        'messages_link',
        'num_sent',
        'num_failed',
        'num_optedout')

    actions = ['mark_incomplete']

    @admin.action(description='Mark selected Notifications broadcasts as INCOMPLETE')
    def mark_incomplete(self, request, queryset):
        updated = queryset.update(status=BroadcastStatus.INCOMPLETE)
        self.message_user(request, ngettext(
            '%d broadcast was successfully marked as INCOMPLETE.',
            '%d broadcasts were successfully marked as INCOMPLETE.',
            updated,
        ) % updated, messages.SUCCESS)

    def messages_link(self, obj):
        num_msgs = obj.messages.count()
        url = resolve_url(admin_urlname(NotificationMessage._meta, SafeText('changelist')))
        return format_html('<a href="{}">{}</a>', f'{url}?broadcast__id={obj.pk}', num_msgs)
    messages_link.short_description = 'Total Messages'

    def num_sent(self, obj):
        return NotificationMessage.objects \
            .filter(broadcast=obj, status=MessageStatus.SENT) \
            .count()
    num_sent.short_description = 'Sent'

    def num_failed(self, obj):
        return NotificationMessage.objects \
            .filter(broadcast=obj, status=MessageStatus.FAILED) \
            .count()
    num_failed.short_description = 'Failed'

    def num_optedout(self, obj):
        return NotificationMessage.objects \
            .filter(broadcast=obj, status=MessageStatus.OPTEDOUT) \
            .count()
    num_optedout.short_description = 'Opted-out'


admin.site.register(NotificationBroadcast, NotificationBroadcastAdmin)
admin.site.register(NotificationMessage, NotificationMessageAdmin)
admin.site.register(NotificationBroadcastConfiguration, SingletonModelAdmin)
