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
from dataclasses import asdict
from smtplib import SMTPException
from typing import Annotated, Iterable, List, NewType, Optional

import pytz
import strawberry
import strawberry_django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import BadSignature, SignatureExpired
from django.db.models import Sum
from django.db.models.functions import Trunc
from django.utils import timezone
from django.utils.translation import gettext as _
from gqlauth.core.exceptions import UserNotVerified
from gqlauth.core.mixins import ArgMixin
from gqlauth.core.types_ import MutationNormalOutput as Output
from gqlauth.core.utils import get_user
from gqlauth.user import arg_mutations as mutations
from gqlauth.user import resolvers
from gqlauth.user.forms import EmailForm
from graphql import GraphQLError
from strawberry_django.permissions import IsAuthenticated

from accounts.mixins import (InviteMemberMixin, RemoveTeamMemberMixin,
                             SignUpMixin, UpdateTeamMemberRoleMixin,
                             UpdateUserMixin)
from accounts.models import Currency, Invitation, Organization, Role, User
from accounts.utils import (TokenScopeError, get_token_payload,
                            get_user_by_email, get_utc_offset,
                            revoke_user_refresh_token)
from landingpage.models import RequestsHistoryAggregate
from lp_server.constants import Messages, TokenAction
from publisher.models import Impression
from publisher.schema import CampaignNode, Connection, ImpressionDataType

UserModel = get_user_model()

USER_NODE_EXCLUDE_FIELDS = [
    'password', 'is_superuser', 'date_joined', 'last_login', 'is_staff',
]

UserRole = strawberry.enum(Role, name='UserRole')
UserCurrency = strawberry.enum(Currency, name='UserCurrency')
UserTimeZone = strawberry.scalar(
    NewType("UserTimeZone", object),
    description="""
    Type that contains user time zone and its UTC offset,
    e.g.:
    {
        displayName: "US/Pacific",
        utc: "-07:00"
    }
    """,
    serialize=lambda v: {
        'displayName': v,
        'utc': get_utc_offset(v)
    },
    parse_value=lambda v: v['displayName']
)


@strawberry_django.type(User, pagination=True, exclude=USER_NODE_EXCLUDE_FIELDS)
class UserNode(strawberry.relay.Node):
    """
    Relay: User Node
    """
    id: strawberry.relay.NodeID[int]
    role: UserRole
    time_zone: UserTimeZone
    currency: UserCurrency
    organization: Annotated['OrganizationNode', strawberry.lazy('accounts.schema')]

    @strawberry.field
    def pk(self) -> int:
        return self.pk

    @strawberry.field
    def time_zone(self) -> UserTimeZone:
        return self.time_zone


@strawberry_django.type(UserModel, pagination=True)
class MinimalUserNode(strawberry.relay.Node):
    """
    Relay: Minmal User Node
    """
    id: strawberry.relay.NodeID[int]
    role: UserRole
    is_active: strawberry.auto
    username: str
    email: str
    first_name: str
    last_name: str
    time_zone: UserTimeZone
    organization: Annotated['OrganizationNode', strawberry.lazy('accounts.schema')]
    invited: strawberry.auto
    currency: UserCurrency

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.select_related('status')

    @strawberry.field
    def pk(self) -> int:
        return self.pk

    @strawberry.field
    def time_zone(self) -> UserTimeZone:
        return self.time_zone


@strawberry.django.filters.filter(Organization, lookups=True)
class OrganizationFilter:
    name: strawberry.auto


@strawberry_django.type(Organization, pagination=True, filters=OrganizationFilter)
class OrganizationNode(strawberry.relay.Node):
    """
    Relay: Organization Node
    """

    id: strawberry.relay.NodeID[int]
    name: strawberry.auto

    @strawberry_django.connection(Connection[MinimalUserNode])
    def users(
        self,
        order_by: Optional[List[Optional[str]]] = strawberry.UNSET
    ) -> Iterable[MinimalUserNode]:
        order = [] if order_by is strawberry.UNSET else order_by
        return UserModel.objects.filter(organization=self).order_by(*order)

    @strawberry_django.connection(Connection[CampaignNode], extensions=[IsAuthenticated()])
    def campaigns(
        self,
        order_by: Optional[List[Optional[str]]] = strawberry.UNSET
    ) -> Iterable[CampaignNode]:
        order = [] if order_by is strawberry.UNSET else order_by
        return self.campaigns.order_by(*order)

    @strawberry.field
    def total_active_campaigns(self) -> Optional[int]:
        return self.campaigns.filter(
            approved=True, enabled=True, draft=False, removed=False).count()

    @strawberry.field
    def last_30_days_impressions(self) -> Optional[int]:
        enddate = timezone.now()
        startdate = enddate - timezone.timedelta(days=30)
        sum = Impression.objects.filter(
            campaign__id__in=self.campaigns.values_list('id', flat=True),
            date__range=[startdate, enddate]) \
            .aggregate(Sum('actual'))['actual__sum']

        return sum if sum else 0

    @strawberry.field
    def total_spending(self, info: strawberry.types.Info) -> Optional[float]:
        user = info.context.request.user

        if user.role != Role.SUPERVISOR:
            raise GraphQLError('Viewer accounts are not authorized to view this value.')

        sum = Impression.objects.filter(
            campaign__id__in=self.campaigns.values_list('id', flat=True)) \
            .aggregate(Sum('actual'))['actual__sum']

        return '%.2f' % (sum * settings.IMPRESSION_BILLING_FACTOR) if sum else 0

    @strawberry.field
    def last_4_days_total_impressions(self) -> Optional[List[Optional[ImpressionDataType]]]:
        enddate = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        startdate = enddate - timezone.timedelta(days=3)
        return RequestsHistoryAggregate.objects \
            .filter(
                campaign__id__in=self.campaigns.values_list('id', flat=True),
                timestamp__range=(startdate, enddate)) \
            .annotate(date=Trunc('timestamp', 'day')) \
            .values('date') \
            .order_by('date') \
            .annotate(total_impressions=Sum('count'))

    @strawberry.field
    def total_impressions(
        self,
        info,
        kind: str,
        start_date: datetime.date,
        end_date: datetime.date
    ) -> Optional[List[Optional[ImpressionDataType]]]:

        user = info.context.request.user
        timezone.activate(user.time_zone)

        if kind not in ['hour', 'day', 'week', 'month', 'year']:
            raise GraphQLError(
                f'kind: "{kind}" is not valid. It has to be "hour", "day", "week", "month" or "year".')

        total_impressions = RequestsHistoryAggregate.objects \
            .filter(
                campaign__id__in=self.campaigns.values_list('id', flat=True),
                timestamp__range=(start_date, end_date)) \
            .annotate(date=Trunc('timestamp', kind)) \
            .values('date') \
            .order_by('date') \
            .annotate(total_impressions=Sum('count'))

        timezone.deactivate()
        return total_impressions


@strawberry_django.type(Invitation, fields='__all__', pagination=True)
class InvitationNode(strawberry.relay.Node):
    """
    Relay: Invitation Node
    """
    pass


@strawberry.type
class UserQuery:
    """
    User Query definition
    """

    @strawberry.field
    def timezones(self) -> List[UserTimeZone]:
        return pytz.common_timezones

    @strawberry.field(extensions=[IsAuthenticated()])
    def organization(
        self,
        info: strawberry.types.Info,
        id: strawberry.ID
    ) -> Optional[OrganizationNode]:
        user = info.context.request.user
        user_org = user.organization

        org = None
        try:
            org = Organization.objects.get(id=id)
        except Organization.DoesNotExist:
            pass

        if user_org != org:
            raise GraphQLError(_('Unauthorized'))

        return org

    @strawberry.field
    def me(self, info: strawberry.types.Info) -> Optional[UserNode]:
        user = get_user(info)
        if not user.is_authenticated:
            return None
        return user  # type: ignore


class SignUp(SignUpMixin, ArgMixin):
    """
    Sign up a new user account
    """

    __doc__ = SignUpMixin.__doc__


class UpdateUser(UpdateUserMixin, ArgMixin):
    """
    Update values of an existing user
    e.g. firstName, lastName, and time zone
    """

    __doc__ = UpdateUserMixin.__doc__


class UpdateTeamMemberRole(UpdateTeamMemberRoleMixin, ArgMixin):
    """
    Update the custom role of an existing team member
    in the same org
    """

    __doc__ = UpdateTeamMemberRoleMixin.__doc__


class InviteMember(InviteMemberMixin, ArgMixin):
    """
    Invite a new member to the organization
    """

    __doc__ = InviteMemberMixin.__doc__


class RemoveTeamMember(RemoveTeamMemberMixin, ArgMixin):
    """
    Remove a team member of the organization
    """

    __doc__ = RemoveTeamMemberMixin.__doc__


class SendPasswordResetEmail(Output, ArgMixin):
    """
    Send a new password reset email
    """

    __doc__ = resolvers.SendPasswordResetEmailMixin.__doc__

    @strawberry.input
    class SendPasswordResetEmailInput:
        email: str

    @classmethod
    def resolve_mutation(cls, info, input_: SendPasswordResetEmailInput) -> Output:
        try:
            email = input_.email
            f = EmailForm({"email": email})
            if f.is_valid():
                user = get_user_by_email(email)
                user.send_password_reset_email(info, [email], jwt_secret=str(user.jwt_secret))
                return cls(success=True)
            return cls(success=False, errors=f.errors.get_json_data())
        except ObjectDoesNotExist:
            return cls(success=True)  # even if user is not registered
        except SMTPException:
            return cls(success=False, errors=Messages.EMAIL_FAIL)
        except UserNotVerified:
            user = get_user_by_email(email)
            try:
                user.status.resend_activation_email(info)
                return cls(
                    success=False,
                    errors={"email": Messages.NOT_VERIFIED_PASSWORD_RESET},)
            except SMTPException:
                return cls(success=False, errors=Messages.EMAIL_FAIL)


class PasswordReset(Output, ArgMixin):
    """
    Reset the password once per link
    """

    __doc__ = resolvers.PasswordResetMixin.__doc__

    form = SetPasswordForm

    @classmethod
    def resolve_mutation(cls, info, input_: resolvers.PasswordResetMixin.PasswordResetInput) -> Output:
        try:
            token = input_.token
            payload = get_token_payload(
                token,
                TokenAction.PASSWORD_RESET,
                settings.GQL_AUTH.EXPIRATION_PASSWORD_RESET_TOKEN)

            user = get_user_model()._default_manager.get(**payload)
            f = cls.form(user, asdict(input_))
            if f.is_valid():
                revoke_user_refresh_token(user)
                user = f.save()

                if user.status.verified is False:
                    user.status.verified = True
                    user.status.save(update_fields=["verified"])

                return cls(success=True)
            return cls(success=False, errors=f.errors.get_json_data())
        except SignatureExpired:
            return cls(success=False, errors=Messages.EXPIRED_TOKEN)
        except (BadSignature, TokenScopeError, get_user_model().DoesNotExist):
            return cls(success=False, errors=Messages.INVALID_TOKEN)


@strawberry.type
class UserMutation:
    """
    User Mutation definition
    """

    sign_up = SignUp.field
    send_password_reset_email = SendPasswordResetEmail.field
    password_reset = PasswordReset.field
    password_change = mutations.PasswordChange.field
    archive_account = mutations.ArchiveAccount.field
    delete_account = mutations.DeleteAccount.field
    update_account = UpdateUser.field
    update_team_member_role = UpdateTeamMemberRole.field
    invite_member = InviteMember.field
    remove_team_member = RemoveTeamMember.field

    token_auth = mutations.ObtainJSONWebToken.field
    verify_token = mutations.VerifyToken.field
    refresh_token = mutations.RefreshToken.field
    revoke_token = mutations.RevokeToken.field
