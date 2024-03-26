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

import strawberry
from typing import Optional, Annotated

from dataclasses import asdict

from django.conf import settings
from django.contrib.auth import get_user_model
from lp_server.constants import Messages

from gqlauth.user.resolvers import RegisterMixin
from gqlauth.core.types_ import MutationNormalOutput as Output
from gqlauth.core.utils import inject_fields

from accounts.decorators import (
    supervisor_role_required, verification_required)
from accounts.forms import (
    SignUpForm, InviteMemberForm, UpdateUserForm,
    UpdateTeamMemberRoleForm, RemoveTeamMemberForm)

from accounts.utils import (
    send_new_user_notification_email, send_invitation_email)

UserModel = get_user_model()


class SignUpMixin(RegisterMixin):
    """
    Sign up user with fields defined in the settings.

    If the email field of the user model is part of the
    registration fields (default), check if there is
    no user with that email or as a secondary email.

    If it exists, it does not register the user,
    even if the email field is not defined as unique
    (default of the default django user model).

    When creating the user, it also creates a `UserStatus`
    related to that user, making it possible to track
    if the user is archived, verified and has a secondary
    email.

    Send account verification email (setting value).

    If allowed to not verify users login, return token.
    """

    form = SignUpForm

    @strawberry.input
    @inject_fields(settings.GQL_AUTH.REGISTER_MUTATION_FIELDS)
    class RegisterInput:
        # We define `org` as a required argument instead of `organization`
        # so that we do not expose the existing organizations to prospective
        # users. Instead, we ask the prospective user to enter their
        # organization name in the `org` field to either add a new
        # organization or join an existing one
        org: str
        password1: str
        password2: str

    @classmethod
    def resolve_mutation(cls, info, input_: RegisterInput) -> Output:
        output = super(SignUpMixin, cls).resolve_mutation(info, input_)

        if output.success:
            # Get the new user object by the given email
            email = input_.email
            new_user = UserModel.objects.get(email=email)

            # Construct the admin recipient list
            admin_list = str(settings.ADMIN_EMAIL_LIST_CSV).replace(' ', '').split(',')

            # Send the new-user notification email
            send_new_user_notification_email(
                info,
                new_user=new_user,
                recipient_list=admin_list)

        return output


class UpdateUserMixin(Output):
    """
    Update the account settings of the authenticated user
    such as their first and last name.

    A verified account is required.
    """

    form = UpdateUserForm

    @strawberry.input
    @inject_fields(settings.GQL_AUTH.UPDATE_MUTATION_FIELDS)
    class UpdateUserInput:
        pass

    @classmethod
    @verification_required
    def resolve_mutation(cls, info, input_: UpdateUserInput) -> Output:
        if all(value is None for value in asdict(input_).values()):
            return cls(success=False, errors=Messages.NO_UPDATE_ARGS)

        user = info.context.request.user

        time_zone = input_.time_zone
        if time_zone and time_zone is not strawberry.UNSET:
            input_.time_zone = time_zone
        else:
            input_.time_zone = user.time_zone
        if time_zone == '':
            return cls(success=False, errors=Messages.INVALID_TIMEZONE)
        first_name = input_.first_name
        if first_name is None:
            input_.first_name = user.first_name

        last_name = input_.last_name
        if last_name is None:
            input_.last_name = user.last_name

        currency = input_.currency
        if currency is strawberry.UNSET or currency is None:
            input_.currency = user.currency

        f = cls.form(asdict(input_), instance=user)
        if f.is_valid():
            f.save()
            return cls(success=True)
        else:
            return cls(success=False, errors=f.errors.get_json_data())


class UpdateTeamMemberRoleMixin(Output):
    """
    Update the role of an existing user.

    A Supervisor role is required for the caller.

    The specified user needs to be in the same
    organization of the caller.
    """

    form = UpdateTeamMemberRoleForm

    @strawberry.input
    class UpdateTeamMemberRoleInput:
        role: Annotated['UserRole', strawberry.lazy('accounts.schema')]
        user_id: int

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: UpdateTeamMemberRoleInput) -> Output:
        user_id = input_.user_id

        org = info.context.request.user.organization

        try:
            user = UserModel.objects.get(id=user_id, organization=org)
        except UserModel.DoesNotExist:
            return cls(success=False, errors=Messages.USER_NOT_FOUND)

        if user == info.context.request.user:
            return cls(success=False, errors=Messages.DOWNGRADE_OWN_ROLE_PROHIBITED)

        f = cls.form(asdict(input_), instance=user)
        if f.is_valid():
            f.save()
            return cls(success=True)
        else:
            return cls(success=False, errors=f.errors.get_json_data())


class InviteMemberMixin(Output):
    """
    Create a new invitation object.

    Send invitation email to the invited email address.

    If there is no user with the requested email,
    a successful response is returned.
    """

    form = InviteMemberForm

    @strawberry.input
    class InviteMemberInput:
        role: Annotated['UserRole', strawberry.lazy('accounts.schema')]
        email: str
        first_name: Optional[str] = strawberry.UNSET
        last_name: Optional[str] = strawberry.UNSET
        organization: Optional[str] = strawberry.UNSET

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: InviteMemberInput) -> Output:
        try:
            user = info.context.request.user

            input_.organization = str(user.organization.pk)
            f = cls.form(asdict(input_))
            if f.is_valid():
                invite = f.save()
                send_invitation_email(info, recipient_list=[invite.email])
                return cls(success=True)
            else:
                return cls(success=False, errors=f.errors.get_json_data())
        except Exception as e:
            return cls(success=False, errors=[{'message': f'{e}', 'code': 'invitation_error'}])


class RemoveTeamMemberMixin(Output):
    """
    Remove an existing user in the organization.

    A Supervisor role is required for the caller.

    The specified user needs to be in the same
    organization of the caller.
    """

    form = RemoveTeamMemberForm

    @strawberry.input
    class RemoveTeamMemberInput:
        is_active: bool
        user_id: int

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: RemoveTeamMemberInput) -> Output:
        user_id = input_.user_id

        org = info.context.request.user.organization

        try:
            user = UserModel.objects.get(id=user_id, organization=org)
        except UserModel.DoesNotExist:
            return cls(success=False, errors=Messages.USER_NOT_FOUND)

        f = cls.form(asdict(input_), instance=user)
        if f.is_valid():
            f.save()
            return cls(success=True)
        else:
            return cls(success=False, errors=f.errors.get_json_data())
