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
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.shortcuts import resolve_url
from django.utils.safestring import SafeText, mark_safe
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.utils.html import format_html

from django.db.models import OuterRef, Exists

from distribution.utils import str2bool
from notification.tasks import add_broadcast_recipients_task
from distribution.models import (
    Vpnuser, OutlineUser, Statistics,
    Issue, AccountDeleteReason, NotificationStatus, OnlineConfig,
    Prefix, LoadBalancer)
from server.models import OutlineServer
from notification.models import NotificationBroadcast


class PurposeForm(ActionForm):
    purpose = forms.CharField(
        required=True,
        empty_value='New broadcast',
        max_length=75)


class OutlineUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'user_channel',
        'request_type',
        'created_date',
        'active',
        'removed',
        'exists_on_server',
        'delete_date',
        'deletion_cause')
    list_display_links = ('id', 'user')
    list_filter = [
        'user__channel',
        'request_type',
        'active',
        'removed',
        'deletion_cause']
    empty_value_display = 'Unknown'
    list_per_page = 10
    list_max_show_all = 100
    search_fields = ['user__username']
    readonly_fields = [
        'request_type',
        'deletion_cause',
        'user']

    def user_channel(self, obj):
        return obj.user.channel

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(user__isnull=True)


class InactiveUserFilter(admin.SimpleListFilter):

    title = 'Inactive Users'
    parameter_name = 'inactive'

    def lookups(self, request, model_admin):
        return (
            ('False', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value():
            if not str2bool(self.value()):
                active = OutlineUser.objects.filter(
                    user=OuterRef('pk'),
                    active=True)
                notremoved = OutlineUser.objects.filter(
                    user=OuterRef('pk'),
                    removed=False)
                return (queryset
                        .filter(outline_keys__isnull=False)
                        .exclude(Exists(active))
                        .filter(Exists(notremoved))
                        .distinct())
        return queryset


class BannedUsersFilter(admin.SimpleListFilter):

    title = 'Banned Users'
    parameter_name = 'banned'

    def lookups(self, request, model_admin):
        return (
            ('True', 'Banned'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(banned=str2bool(self.value()))
        return queryset


class InactiveServerUsersFilter(admin.SimpleListFilter):

    title = 'Inactive Servers'
    parameter_name = 'server'

    def lookups(self, request, model_admin):

        servers = OutlineServer.objects.filter(
            active=False,
            is_distributing=True,
        )
        server_list = []
        for server in servers:
            if server.ipv4:
                server_list.append((server.id, server.ipv4))
            elif server.ipv6:
                server_list.append((server.id, server.ipv6))

        return server_list

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(outline_keys__server=self.value())
        return queryset


class BlockedServerUsersFilter(admin.SimpleListFilter):

    title = 'Blocked Servers'
    parameter_name = 'server'

    def lookups(self, request, model_admin):

        servers = OutlineServer.objects.filter(
            active=True,
            is_distributing=True,
            is_blocked=True
        )
        server_list = []
        for server in servers:
            if server.ipv4:
                server_list.append((server.id, server.ipv4))
            elif server.ipv6:
                server_list.append((server.id, server.ipv6))

        return server_list

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(outline_keys__server=self.value())
        return queryset


class ServerUsersFilter(admin.SimpleListFilter):

    title = 'Specific Server'
    parameter_name = 'server'

    def lookups(self, request, model_admin):

        servers = OutlineServer.objects.filter(
            active=True,
            is_distributing=True,
        )
        server_list = []
        for server in servers:
            if server.ipv4:
                server_list.append((server.id, server.ipv4))
            elif server.ipv6:
                server_list.append((server.id, server.ipv6))

        return server_list

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(outline_keys__server=self.value())
        return queryset


class VpnuserAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'username',
        'channel',
        'created_date',
        'delete_date')
    list_display_links = ('id', 'username')
    list_filter = (
        'channel',
        'region',
        ServerUsersFilter,
        BlockedServerUsersFilter,
        InactiveServerUsersFilter,
        BannedUsersFilter,
        InactiveUserFilter,
    )
    empty_value_display = 'unknown'
    list_per_page = 10
    list_max_show_all = 100
    search_fields = ['username']
    actions = ['create_broadcast_list']
    action_form = PurposeForm

    @admin.action(
        description='Create a new broadcast with selected recipients')
    def create_broadcast_list(self, request, queryset):
        # filtering users with `notification_status=NotificationStatus.ENABLED`, notification_status is set for
        # 'blocked' or 'deactivated' telegram accounts
        queryset = queryset.filter(notification_status=NotificationStatus.ENABLED)
        total_users = queryset.count()

        purpose = request.POST.get('purpose', '')

        if purpose != '':
            # Create a new pending notification broadcast
            broadcast = NotificationBroadcast.objects.create(
                purpose=purpose)

            user_ids = queryset.values_list('id', flat=True)

            # Run as a celery task
            add_broadcast_recipients_task.delay(broadcast.id, list(user_ids))

            url = resolve_url(admin_urlname(broadcast._meta, SafeText('change')), broadcast.pk)
            new_bc_html_link = format_html('<a href="{}">{}</a>', url, 'new PENDING notification broadcast')
            self.message_user(
                request,
                mark_safe(f'{total_users} users are being added to a {new_bc_html_link}'),
                messages.SUCCESS)
        else:
            self.message_user(
                request,
                'Please add a purpose for the new broadcast!',
                messages.ERROR)


@admin.register(Prefix)
class PrefixAdmin(admin.ModelAdmin):

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'prefix_str':
            kwargs['strip'] = False
        return super().formfield_for_dbfield(db_field, request, **kwargs)


admin.site.register(Issue)
admin.site.register(AccountDeleteReason)
admin.site.register(OutlineUser, OutlineUserAdmin)
admin.site.register(Vpnuser, VpnuserAdmin)
admin.site.register(Statistics)
admin.site.register(OnlineConfig)
admin.site.register(LoadBalancer)
