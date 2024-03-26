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
import inspect
from typing import (TYPE_CHECKING, Annotated, Any, Iterable, List, Optional,
                    cast)

import pytz
import strawberry
import strawberry_django
from django.conf import settings
from django.db.models import Count, Sum
from django.db.models.functions import Trunc
from django.utils import timezone
from gqlauth.core.mixins import ArgMixin
from graphql import GraphQLError
from strawberry.relay.types import NodeIterableType
from strawberry.relay.utils import from_base64, to_base64
from strawberry.types.info import Info
from strawberry.utils.await_maybe import AwaitableOrValue
from strawberry_django import relay
from strawberry_django.pagination import OffsetPaginationInput
from strawberry_django.permissions import IsAuthenticated
from typing_extensions import Self

from accounts.models import Role
from landingpage.models import RequestsHistory, RequestsHistoryAggregate
from preference.schema import RegionFilter, RegionNode
from publisher.mixins import (CreateCampaignMixin, DeleteCampaignMixin,
                              DisableCampaignMixin, DuplicateCampaignMixin,
                              EnableCampaignMixin)
from publisher.models import (Campaign, CampaignConsumptionHistory,
                              CampaignFundingHistory, Impression, PlanType)

CampaignPlanType = strawberry.enum(PlanType, name='CampaignPlanType')


@strawberry.type
class Connection(relay.ListConnectionWithTotalCount[strawberry.relay.NodeType]):
    """
    A strawberry connection to count the number of query results
    """

    @strawberry.field
    def edge_count(root, info: Info) -> Optional[int]:
        return len(root.edges)

    # Adding offset argument to custom connection
    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[strawberry.relay.NodeType],
        *,
        info: Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        offset: Optional[int] = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[Self]:

        # This implemntation is based on the graphene
        # implementation of first/offset pagination
        if offset:
            if after:
                offset += from_base64(after) + 1
            # input offset starts at 1 while the offset starts at 0
            after = to_base64("arrayconnection", offset - 1)

        conn = super().resolve_connection(
            nodes,
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
            **kwargs,
        )

        if inspect.isawaitable(conn):

            async def wrapper():
                resolved = await conn
                resolved.nodes = nodes
                return resolved

            return wrapper()

        conn = cast(Self, conn)
        conn.nodes = nodes
        return conn


@strawberry.django.filters.filter(Impression, lookups=True)
class ImpressionFilter:
    date: strawberry.auto


@strawberry_django.type(Impression, pagination=True, filters=ImpressionFilter)
class ImpressionNode(strawberry.relay.Node):
    """
    Relay: Impression Node
    """

    id: strawberry.relay.NodeID[int]
    campaign: Annotated['CampaignNode', strawberry.lazy('publisher.schema')]
    percentage: strawberry.auto
    desired: strawberry.auto
    actual: strawberry.auto
    date: strawberry.auto

    @strawberry.field
    def budget_spent(self) -> Optional[float]:
        return '%.2f' % (self.actual * settings.IMPRESSION_BILLING_FACTOR)


@strawberry.type
class ImpressionDataType:
    """
    Relay: Impression Data Type
    """

    @strawberry.field
    def date(self) -> datetime.datetime:
        return self['date']

    @strawberry.field
    def total_impressions(self) -> int:
        return self['total_impressions']

    @strawberry.field
    def total_spending(self, info: strawberry.types.Info) -> Optional[float]:
        user = info.context.request.user

        if user.role != Role.SUPERVISOR:
            raise GraphQLError('Viewer accounts are not authorized to view this value.')

        imps = self['total_impressions']

        return '%.2f' % (imps * settings.IMPRESSION_BILLING_FACTOR) if imps else 0


@strawberry.django.filters.filter(RequestsHistoryAggregate, lookups=True)
class RequestFilter:
    timestamp: strawberry.auto


@strawberry_django.type(RequestsHistoryAggregate, pagination=True, filters=RequestFilter)
class RequestNode(strawberry.relay.Node):
    """
    Relay: Requests Node
    """

    id: strawberry.relay.NodeID[int]
    timestamp: strawberry.auto


@strawberry.django.filters.filter(Campaign, lookups=True)
class CampaignFilter:

    if TYPE_CHECKING:
        from accounts.schema import OrganizationFilter

    unique_id: strawberry.auto
    organization: Optional[Annotated['OrganizationFilter', strawberry.lazy('accounts.schema')]]
    name: Optional[str]
    plan_type: Optional[CampaignPlanType]
    target_regions: Optional[RegionFilter]
    start_date: Optional[datetime.date]
    end_date: Optional[datetime.date]
    approved: strawberry.auto
    enabled: strawberry.auto
    draft: strawberry.auto
    removed: strawberry.auto

    def filter_organization_id(self, queryset):
        if self.organization_id in (None, strawberry.UNSET):
            return queryset

        if self.organization_id:
            queryset = queryset.filter(organization__pk=self.organization_id)
        else:
            queryset = queryset.exclude(organization__pk=self.organization_id)

        return queryset


@strawberry_django.type(Campaign, pagination=True, filters=CampaignFilter)
class CampaignNode(strawberry.relay.Node):
    """
    Relay: Campaign Node
    """
    if TYPE_CHECKING:
        from accounts.schema import OrganizationNode

    id: strawberry.relay.NodeID[int]
    unique_id: strawberry.auto
    name: str
    organization: Annotated['OrganizationNode', strawberry.lazy('accounts.schema')]
    plan_type: CampaignPlanType
    impression_per_period: strawberry.auto
    target_url: Optional[str]
    has_website: strawberry.auto
    source: Optional[str]
    medium: Optional[str]
    approved: strawberry.auto
    enabled: strawberry.auto
    draft: strawberry.auto
    removed: strawberry.auto

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = info.context.request.user
        user_org = user.organization

        return queryset.filter(organization=user_org)

    @strawberry.field(extensions=[IsAuthenticated()])
    def initial_date(self, info) -> Optional[str]:
        user = info.context.request.user
        time_zone = pytz.timezone(user.time_zone)
        # Convert UTC time to user time zone and return date excluding time
        return timezone.localtime(self.initial_date, time_zone).strftime('%Y-%m-%d')

    @strawberry.field(extensions=[IsAuthenticated()])
    def start_date(self, info) -> Optional[str]:
        user = info.context.request.user
        time_zone = pytz.timezone(user.time_zone)
        # Convert UTC time to user time zone and return date excluding time
        return timezone.localtime(self.start_date, time_zone).strftime('%Y-%m-%d')

    @strawberry.field(extensions=[IsAuthenticated()])
    def end_date(self, info) -> Optional[str]:

        # When monthly campaigns are created end_date should return None
        if not self.end_date:
            return None

        user = info.context.request.user
        time_zone = pytz.timezone(user.time_zone)
        # Convert UTC time to user time zone and return date excluding time
        return timezone.localtime(self.end_date, time_zone).strftime('%Y-%m-%d')

    @strawberry.field(extensions=[IsAuthenticated()])
    def target_regions(self) -> Optional[List[Optional[RegionNode]]]:
        return self.target_regions.all()

    @strawberry_django.connection(Connection[ImpressionNode], extensions=[IsAuthenticated()])
    def impressions(
        self,
        order_by: Optional[List[Optional[str]]] = strawberry.UNSET,
        pagination: Optional[OffsetPaginationInput] = strawberry.UNSET
    ) -> Iterable[ImpressionNode]:
        order = [] if order_by is strawberry.UNSET else order_by
        qs = self.daily_plans.order_by(*order)
        return strawberry_django.pagination.apply(pagination, qs)

    @strawberry_django.connection(Connection[RequestNode], extensions=[IsAuthenticated()])
    def requests(
        self,
        order_by: Optional[List[Optional[str]]] = strawberry.UNSET,
        pagination: Optional[OffsetPaginationInput] = strawberry.UNSET
    ) -> Iterable[RequestNode]:
        order = [] if order_by is strawberry.UNSET else order_by
        qs = self.hourly_requests.order_by(*order)
        return strawberry_django.pagination.apply(pagination, qs)

    @strawberry.field
    def daily_budget(self) -> Optional[float]:
        daily_budget = 0
        daily_plan = self.daily_plans.first()
        if daily_plan:
            daily_budget = '%.2f' % (self.daily_plans.first().desired * settings.IMPRESSION_BILLING_FACTOR)
        return daily_budget

    @strawberry.field
    def budget_spent(self) -> Optional[float]:
        actual_impressions_sum = 0
        daily_plans = self.daily_plans.all()
        if daily_plans:
            actual_impressions_sum = daily_plans.aggregate(Sum('actual'))['actual__sum']
        return '%.2f' % (actual_impressions_sum * settings.IMPRESSION_BILLING_FACTOR)

    @strawberry.field(extensions=[IsAuthenticated()])
    def total_impressions(
        self,
        info,
        kind: str,
        start_date: datetime.date,
        end_date: datetime.date,
        source_id: Optional[int] = None
    ) -> Optional[List[Optional[ImpressionDataType]]]:

        user = info.context.request.user
        timezone.activate(user.time_zone)

        if kind not in ['hour', 'day', 'week', 'month', 'year']:
            raise GraphQLError(
                f'kind: "{kind}" is not valid. It has to be "hour", "day", "week", "month" or "year".')

        filters = {
            'campaign_id': self.id,
            'timestamp__range': (start_date, end_date)
        }
        if source_id:
            filters['source'] = source_id

        qs = list(
            RequestsHistoryAggregate.objects
            .filter(**filters)
            .annotate(date=Trunc('timestamp', kind))
            .values('date')
            .order_by('date')
            .annotate(total_impressions=Sum('count')))

        if kind == 'hour':
            # This is needed because we aggregate the requests hourly on the hour
            # and not in real time so the current_hour requests has to be added to the list
            # of aggregate results
            current_hour = timezone.now().replace(minute=0, second=0, microsecond=0)

            filters = {
                'campaign_id': self.id,
                'created__gte': current_hour
            }
            if source_id:
                filters['source'] = source_id
            current_hour_imps = list(
                RequestsHistory.objects
                .filter(**filters)
                .annotate(date=Trunc('created', 'hour'))
                .values('date')
                .order_by('date')
                .annotate(total_impressions=Count('id')))
            qs = qs + current_hour_imps

        timezone.deactivate()
        return qs


@strawberry.django.filters.filter(CampaignFundingHistory, lookups=True)
class CampaignFundingHistoryFilter:

    campaign_id: strawberry.auto
    # campaign__name: strawberry.auto
    amount: strawberry.auto
    payment_date: strawberry.auto
    payment_confirmation: strawberry.auto


@strawberry_django.type(CampaignFundingHistory, pagination=True, filters=CampaignFundingHistoryFilter)
class CampaignFundingHistoryNode(strawberry.relay.Node):
    """
    Relay: Campaign Funding History Node
    """

    id: strawberry.relay.NodeID[int]
    campaign: strawberry.auto
    amount: strawberry.auto
    payment_date: strawberry.auto
    payment_confirmation: strawberry.auto


@strawberry.django.filters.filter(CampaignConsumptionHistory, lookups=True)
class CampaignConsumptionHistoryFilter:

    campaign_id: strawberry.auto
    # campaign__name: strawberry.auto
    invoice_id: strawberry.auto
    consumption_date: strawberry.auto
    number_of_impression: strawberry.auto
    consumed_amount: strawberry.auto


@strawberry_django.type(CampaignConsumptionHistory, pagination=True, filters=CampaignConsumptionHistoryFilter)
class CampaignConsumptionHistoryNode(strawberry.relay.Node):
    """
    Relay: Campaign Consumption History Node
    """

    id: strawberry.relay.NodeID[int]
    campaign: strawberry.auto
    invoice_id: strawberry.auto
    consumption_date: strawberry.auto
    number_of_impression: strawberry.auto
    consumed_amount: strawberry.auto


@strawberry.type
class PublisherQuery:
    """
    Publisher Query definition
    """

    daily_plan: ImpressionNode = strawberry_django.field(extensions=[IsAuthenticated()])
    daily_plans: Connection[ImpressionNode] = strawberry_django.connection(extensions=[IsAuthenticated()])

    # TODO: Reactivate in the next phase if needed
    # fund: CampaignFundingHistoryNode = strawberry_django.field(extensions=[IsAuthenticated()])
    # funds: Connection[CampaignFundingHistoryNode] = strawberry_django.connection(extensions=[IsAuthenticated()])

    # TODO: Reactivate in the next phase if needed
    # consumption: CampaignConsumptionHistoryNode = strawberry_django.field(extensions=[IsAuthenticated()])
    # consumptions: Connection[CampaignConsumptionHistoryNode] = strawberry_django.connection(extensions=[IsAuthenticated()])

    @strawberry.field(extensions=[IsAuthenticated()])
    def campaign(self, info: strawberry.types.Info, unique_id: str) -> Optional[CampaignNode]:
        campaign = None
        try:
            campaign = Campaign.objects.get(
                unique_id__iexact=unique_id,
                organization=info.context.request.user.organization)
        except Campaign.DoesNotExist:
            pass

        return campaign

    @strawberry.field(extensions=[IsAuthenticated()])
    def campaigns(
        self,
        info: strawberry.types.Info,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List[Optional[str]]] = strawberry.UNSET,
        filters: Optional[CampaignFilter] = strawberry.UNSET
    ) -> Optional[Connection[CampaignNode]]:
        user = info.context.request.user
        order = [] if order_by is strawberry.UNSET else order_by
        qs = Campaign.objects.filter(organization=user.organization).order_by(*order)
        qs = strawberry_django.filters.apply(filters, qs)
        return Connection[CampaignNode].resolve_connection(info=info, nodes=qs, offset=offset, first=first, last=last, after=after, before=before)


class CreateCampaign(CreateCampaignMixin, ArgMixin):
    """
    Create a new campaign
    """

    __doc__ = CreateCampaignMixin.__doc__


class DuplicateCampaign(DuplicateCampaignMixin, ArgMixin):
    """
    Duplicate an existing campaign
    """

    __doc__ = DuplicateCampaignMixin.__doc__


class DeleteCampaign(DeleteCampaignMixin, ArgMixin):
    """
    Delete an existing campaign
    """

    __doc__ = DeleteCampaignMixin.__doc__


class EnableCampaign(EnableCampaignMixin, ArgMixin):
    """
    Enable a disabled approved campaign
    """

    __doc__ = EnableCampaignMixin.__doc__


class DisableCampaign(DisableCampaignMixin, ArgMixin):
    """
    Disable an enabled approved campaign
    """

    __doc__ = DisableCampaignMixin.__doc__


@strawberry.type
class PublisherMutation:
    """
    Publisher Mutations
    """

    create_campaign = CreateCampaign.field
    duplicate_campaign = DuplicateCampaign.field
    delete_campaign = DeleteCampaign.field
    enable_campaign = EnableCampaign.field
    disable_campaign = DisableCampaign.field

    @strawberry.mutation
    def suggest_campaign_unique_id(self, campaign_name: str) -> str:
        """
        Suggest a Campaign UniqueId based on the campaign name
        """
        unique_id = ('-').join(campaign_name.split()).lower()

        # Check to see if a campaign with the same suggested unique_id exists
        try:
            Campaign.objects.get(unique_id=unique_id)
        except Campaign.DoesNotExist:
            return unique_id

        # Append '-1' if a campaign with the same unique_id exists
        unique_id += '-1'
        return unique_id
