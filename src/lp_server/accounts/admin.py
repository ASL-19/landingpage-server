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

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    UserChangeForm, UserCreationForm)

from accounts.models import (
    User, Organization, Invitation)

from gqlauth.models import UserStatus

from accounts.utils import send_new_verification_notification_email


STATUS_HELP_TEXT = ' '.join([
    'Please note that enabling the',
    '<strong>Verified</strong> status will',
    'trigger sending a welcome email',
    'directed to the email of this user',
    'and activate their account',
    '(allow the user to login to BeePass Campaigns).'])


class UserStatusAdmin(admin.StackedInline):
    model = UserStatus

    fieldsets = [
        (None, {
            'fields': ('verified', 'archived', ),
            'description': STATUS_HELP_TEXT,
        }),
    ]


class CustomUserCreateForm(UserCreationForm):
    """
    Custom User creation form
    """

    class Meta(UserCreationForm.Meta):
        model = User


class CustomUserChangeForm(UserChangeForm):
    """
    Custom User change form
    """

    class Meta(UserChangeForm.Meta):
        model = User


class UserAdmin(UserAdmin):
    """
    Custom User admin panel
    """
    add_form = UserCreationForm

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'organization',
                'first_name',
                'last_name',
                'username',
                'email',
                'password1',
                'password2',
            ),
        }),
    )

    form = CustomUserChangeForm

    extra_user_fields = (
        'organization',
        'role',
        'time_zone',
        'currency',
        'invited',
    )

    list_display = [
        'username',
        'email',
        'organization',
        'first_name',
        'last_name',
        'is_superuser',
        'role',
        'verified',
    ]

    for fieldset in UserAdmin.fieldsets:
        if fieldset[0] == 'Permissions':
            fieldset[1]['fields'] += 'monitoring_access',
            break

    fieldsets = UserAdmin.fieldsets + (
        ('uSponsorship Dashboard User Details', {'fields': extra_user_fields}),
    )

    readonly_fields = ('invited',)

    list_filter = UserAdmin.list_filter + (
        'organization',
    )

    inlines = [
        UserStatusAdmin,
    ]

    def verified(self, obj):
        return obj.status.verified
    verified.boolean = True
    verified.admin_order_field = 'status__verified'
    verified.short_description = 'Verified'

    # Only show the User status inline on the change form
    def get_inlines(self, request, obj=None):
        if obj:
            return [UserStatusAdmin, ]
        else:
            return []

    def save_formset(self, request, form, formset, change):
        """
        `form` is the base User form
        `formset` is the ("UserStatus") formset to save
        `change` is True if you are editing an existing User,
                    False if you are creating a new User
        """

        user = form.instance

        # If a user gets verified by the admin, notify the user
        # if the `send_activation_email` setting was false and
        # the user has an email address
        if settings.GQL_AUTH.SEND_ACTIVATION_EMAIL is False and user.EMAIL_FIELD:
            if user.pk is not None:
                original = User.objects.get(pk=user.pk)

                if (hasattr(original, 'status') and
                        original.status.verified != user.status.verified and
                        user.status.verified is True):
                    send_new_verification_notification_email(request, new_user=user)

        super().save_formset(request, form, formset, change)


class OrganizationAdmin(admin.ModelAdmin):
    """
    Organization admin panel definition
    """

    list_display = (
        'name',
    )

    ordering = (
        'name',
    )


class InvitationAdmin(admin.ModelAdmin):
    """
    Invitation admin panel definition
    """

    list_display = (
        'organization',
        'invitee_full_name',
        'email',
        'created',
        'accepted',
    )

    ordering = (
        'organization__name',
        'first_name',
    )

    list_filter = (
        'organization',
    )

    def invitee_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'
    invitee_full_name.admin_order_field = 'first_name'
    invitee_full_name.short_description = 'Invitee Name'


admin.site.register(User, UserAdmin)
admin.site.unregister(UserStatus)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Invitation, InvitationAdmin)
