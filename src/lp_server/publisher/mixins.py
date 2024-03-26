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

import pytz

import strawberry
from typing import Optional, Annotated, List

from dataclasses import asdict

from django.db import transaction
from django.db.utils import IntegrityError
from copy import deepcopy

from lp_server.helpers import validate_url, to_user_datetime
from accounts.decorators import supervisor_role_required
from publisher.forms import CreateCampaignForm
from lp_server.constants import Messages

from gqlauth.core.types_ import MutationNormalOutput as Output

from publisher.utils import validate_dates

from publisher.models import Campaign


@strawberry.type
class CreateCampaignMixin(Output):
    """
    Create a new campaign

    #### Args Ex:

    name: "test 1"

    uniqueId: "test-1-campaign"
    **only lowercase [a-z], digits, and hyphens**

    targetUrl: "https://asl19.org"
    **https only**

    planType: "1"
    **ONE-TIME (1) or MONTHLY (2)**

    source: "beepass"

    medium: "vpn"

    regionsList: "mena, iran"

    startDate: "2021-01-22"
    **YYY-MM-DD date format**

    impressionPerPeriod: 20000
    """

    form = CreateCampaignForm

    @strawberry.input
    class CreateCampaignInput:
        name: str
        unique_id: str
        source: Optional[str] = None
        medium: Optional[str] = None
        regions_list: str
        plan_type: Annotated['CampaignPlanType', strawberry.lazy('publisher.schema')]
        start_date: str
        impression_per_period: int
        target_url: Optional[str] = None
        end_date: Optional[str] = None
        draft: Optional[bool] = False
        has_website: Optional[bool] = True

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: CreateCampaignInput) -> Output:
        try:
            user = info.context.request.user
            time_zone = pytz.timezone(user.time_zone)

            f = cls.form(asdict(input_))
            if f.is_valid():
                plan_type = input_.plan_type
                start_date = input_.start_date
                end_date = input_.end_date

                parsed_start_date = to_user_datetime(start_date, time_zone)

                parsed_end_date = None
                if end_date is not None:
                    parsed_end_date = to_user_datetime(end_date, time_zone)

                # Check to see if the start and end dates are logical
                # and in accordance with to the plan type
                dates_validation_error = validate_dates(
                    plan_type, parsed_start_date, end_date, parsed_end_date)

                if dates_validation_error is not None:
                    return cls(success=False, errors=dates_validation_error)

                with transaction.atomic():
                    f.save(
                        user=user,
                        parsed_start_date=parsed_start_date,
                        parsed_end_date=parsed_end_date)

                return cls(success=True)
            else:
                return cls(success=False, errors=f.errors.get_json_data())
        except IntegrityError as e:
            if e.__cause__.pgcode == '23505':  # Duplicate key value violates unique constraint for unique_id
                return cls(success=False, errors=Messages.UNIQUE_ID_USED)
            else:
                return cls(
                    success=False,
                    errors=[{'message': f'IntegrityError: {e}', 'code': 'campaign_creation_error'}])
        except Exception as e:
            return cls(success=False, errors=[{'message': f'{e}', 'code': 'campaign_creation_error'}])


@strawberry.type
class DuplicateCampaignMixin(Output):
    """
    Duplicate an existing campaign by its uniqueId.

    The uniqueId of the new campaign will be the same as the
    original one suffixed with `.copy{count}`, e.g. copy1
    """

    @strawberry.input
    class DuplicateCampaignInput:
        original_campaign_unique_id: str
        new_name: str
        new_target_url: Optional[str] = None
        new_start_date: Optional[str] = None
        new_end_date: Optional[str] = None

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: DuplicateCampaignInput) -> Output:
        try:
            user = info.context.request.user
            time_zone = pytz.timezone(user.time_zone)

            original_campaign_unique_id = input_.original_campaign_unique_id

            with transaction.atomic():
                original_campaign = Campaign.objects.get(unique_id__exact=original_campaign_unique_id)

                if user.organization == original_campaign.organization:
                    dup_count = Campaign.objects \
                        .filter(unique_id__icontains=original_campaign.unique_id) \
                        .count()
                    original_campaign.unique_id = f'{original_campaign.unique_id}-copy{dup_count}'

                    plan_type = original_campaign.plan_type
                    original_campaign.name = input_.new_name
                    new_target_url = input_.new_target_url
                    new_start_date = input_.new_start_date
                    new_end_date = input_.new_end_date

                    parsed_start_date = original_campaign.start_date
                    parsed_end_date = original_campaign.end_date  # None for monthly campaigns

                    # Overwrite the original target URL if a new target URL was provided
                    if new_target_url is not None:
                        validate_url(new_target_url)
                        original_campaign.target_url = new_target_url

                    # Overwrite the original start date if a new start date was provided
                    # and parse the new start date string into a datetime.datetime object
                    # for error handling
                    if new_start_date is not None:
                        parsed_start_date = to_user_datetime(new_start_date, time_zone)
                        original_campaign.start_date = parsed_start_date

                    # Overwrite the original end date if a new end date was provided
                    # and parse the new end date string into a datetime.datetime object
                    # for error handling
                    if new_end_date is not None:
                        parsed_end_date = to_user_datetime(new_end_date, time_zone)
                        original_campaign.end_date = parsed_end_date

                    # Check to see if the new start and end dates are logical
                    # and in accordance with to the plan type
                    dates_validation_error = validate_dates(
                        plan_type, parsed_start_date, new_end_date, parsed_end_date)

                    if dates_validation_error is not None:
                        return cls(success=False, errors=dates_validation_error)

                    # The new copy has to be approved by ASL19 admin
                    original_campaign.approved = False

                    target_regions = original_campaign.target_regions.all()

                    # Duplicate the original campaign into a new campaign
                    duplicate = deepcopy(original_campaign)
                    duplicate.id = None
                    duplicate.save()

                    # Copy the many-to-many target_regions over to the duplicate
                    duplicate.target_regions.add(*target_regions)

                    return cls(success=True)
                else:
                    return cls(success=False, errors=Messages.ORGANIZATION_NOT_MATCHING)
        except Exception as e:
            return cls(success=False, errors=[{'message': f'{e}', 'code': 'campaign_duplication_error'}])


@strawberry.type
class DeleteCampaignMixin(Output):
    """
    Remove an existing campaign by its uniqueId.

    This will enable the `removed` boolean of the campaign and will not actually delete
    the campaign object itself.
    """

    @strawberry.input
    class DeleteCampaignInput:
        campaign_unique_ids: List[str]

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: DeleteCampaignInput) -> Output:
        try:
            user = info.context.request.user

            campaign_unique_ids = input_.campaign_unique_ids
            for campaign_unique_id in campaign_unique_ids:
                campaign = Campaign.objects.get(unique_id__exact=campaign_unique_id)

                if user.organization == campaign.organization:

                    if campaign.removed is True:
                        return cls(success=False, errors=Messages.CAMPAIGN_AlREADY_REMOVED)
                    elif campaign.enabled is True and campaign.approved is True:
                        return cls(success=False, errors=Messages.CAMPAIGN_NOT_DISABLED)
                else:
                    return cls(success=False, errors=Messages.ORGANIZATION_NOT_MATCHING)

            with transaction.atomic():
                for campaign_unique_id in campaign_unique_ids:
                    campaign = Campaign.objects.get(unique_id__exact=campaign_unique_id)
                    campaign.removed = True
                    campaign.save()

                return cls(success=True)
        except Exception as e:
            return cls(success=False, errors=[{'message': f'{e}', 'code': 'campaign_deletion_error'}])


@strawberry.type
class EnableCampaignMixin(Output):
    """
    Enable (activate) a campaign by its uniqueId.

    The campaign to be enabled has to be approved and disabled.
    Pending, expired, removed, or draft campaigns cannot be enabled nor disabled.
    """

    @strawberry.input
    class EnableCampaignInput:
        campaign_unique_id: str

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: EnableCampaignInput) -> Output:
        try:
            user = info.context.request.user

            campaign_unique_id = input_.campaign_unique_id
            with transaction.atomic():
                campaign = Campaign.objects.get(unique_id__exact=campaign_unique_id)

                if user.organization == campaign.organization:
                    if campaign.removed is True:
                        return cls(success=False, errors=Messages.CAMPAIGN_AlREADY_REMOVED)
                    elif campaign.approved is False:
                        return cls(success=False, errors=Messages.CAMPAIGN_NOT_APPROVED)
                    elif campaign.enabled is True:
                        return cls(success=False, errors=Messages.CAMPAIGN_ALREADY_ENABLED)

                    campaign.enabled = True
                    campaign.save()

                    return cls(success=True)
                else:
                    return cls(success=False, errors=Messages.ORGANIZATION_NOT_MATCHING)
        except Exception as e:
            return cls(success=False, errors=[{'message': f'{e}', 'code': 'campaign_activation_error'}])


@strawberry.type
class DisableCampaignMixin(Output):
    """
    Disable (pause) a campaign by its uniqueId.

    The campaign to be disabled has to be approved and enabled.
    Pending, expired, removed, or draft campaigns cannot be enabled nor disabled.
    """

    @strawberry.input
    class DisableCampaignInput:
        campaign_unique_id: str

    @classmethod
    @supervisor_role_required
    def resolve_mutation(cls, info, input_: DisableCampaignInput) -> Output:
        try:
            user = info.context.request.user

            campaign_unique_id = input_.campaign_unique_id

            with transaction.atomic():
                campaign = Campaign.objects.get(unique_id__exact=campaign_unique_id)

                if user.organization == campaign.organization:
                    if campaign.removed is True:
                        return cls(success=False, errors=Messages.CAMPAIGN_AlREADY_REMOVED)
                    elif campaign.approved is False:
                        return cls(success=False, errors=Messages.CAMPAIGN_NOT_APPROVED)
                    elif campaign.enabled is False:
                        return cls(success=False, errors=Messages.CAMPAIGN_ALREADY_DISABLED)

                    campaign.enabled = False
                    campaign.save()

                    return cls(success=True)
                else:
                    return cls(success=False, errors=Messages.ORGANIZATION_NOT_MATCHING)
        except Exception as e:
            return cls(success=False, errors=[{'message': f'{e}', 'code': 'campaign_deactivation_error'}])
