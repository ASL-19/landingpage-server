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
from django import forms
from django.contrib.auth import get_user_model

from gqlauth.user.forms import (
    RegisterForm, UpdateAccountForm)
from accounts.models import (
    Organization, Role, Invitation)

logger = logging.getLogger(__name__)


class SignUpForm(RegisterForm):
    """
    Sign up form that is the base
    form for the signUp GraphQL mutation
    """

    # Enforce org, first_name, and last_name to be required
    org = forms.CharField(max_length=32, required=True)
    first_name = forms.CharField(max_length=32, required=True)
    last_name = forms.CharField(max_length=32, required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        orgname = self.cleaned_data['org']

        try:
            # get or create an organization based on the submitted org
            org, created = Organization.objects.get_or_create(name=orgname)
            if org.users.count() == 0:
                # give the first user in the organization a supervisor role
                # instead of the default viewer role
                user.role = Role.SUPERVISOR

            # assign the organization as the user's organization
            user.organization = org
        except Exception as e:
            logger.error(f'Associating organization to user has failed: ({(e)})')

        if commit:
            user.save()

        return user


class UpdateUserForm(UpdateAccountForm):
    """
    Update User form that is the base
    form for the updateAccount GraphQL mutation
    """

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        # A user's time_zone and currency should be optional to change
        # in the form associated with the mutation
        self.fields['time_zone'].required = False
        self.fields['currency'].required = False


class UpdateTeamMemberRoleForm(forms.ModelForm):
    """
    Update User form that is the base
    form for the updateTeamMemberRole GraphQL mutation
    """

    class Meta:
        model = get_user_model()
        fields = ('role',)


class InviteMemberForm(forms.ModelForm):
    """
    Invite member form that is the base
    form for the inviteMember GraphQL mutation
    """

    class Meta:
        model = Invitation
        fields = (
            'first_name', 'last_name', 'email', 'role', 'organization'
        )


class RemoveTeamMemberForm(forms.ModelForm):
    """
    Update User form that is the base
    form for the removeTeamMember GraphQL mutation
    """

    class Meta:
        model = get_user_model()
        fields = ('is_active',)
