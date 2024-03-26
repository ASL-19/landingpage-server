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
from publisher.models import Campaign
from preference.models import Region


class CreateCampaignForm(forms.ModelForm):
    """
    Create Campaign form that is the base form for the createCampaign GraphQL mutation
    """

    # We define regions_list instead of the existing
    # model field 'target_regions' to allow for accepting
    # a list of region names such as "Iran, MENA" when
    # calling the mutation instead of providing a list
    # of primary keys (pk) of regions
    # Note that the field is required in the mutation
    # (CreateCampaign) regardless of its required status
    # here in the form
    regions_list = forms.CharField(max_length=64)

    class Meta:
        model = Campaign
        fields = (
            'name',
            'unique_id',
            'target_url',
            'has_website',
            'medium',
            'source',
            'plan_type',
            'impression_per_period',
            'draft',
        )
        exclude = (
            'organization',
            'target_regions',
            'approved',
            'enabled',
        )

    def clean_regions_list(self):
        data = self.cleaned_data
        regions_list = data.get('regions_list', None)

        if regions_list is not None:
            for region_name in regions_list.split(','):
                try:
                    Region.objects.get(name__iexact=region_name.strip())
                except Region.DoesNotExist:
                    raise forms.ValidationError(f"Region '{region_name}' does not exist", 'not_existing_region')
        return regions_list

    def save(self, commit=True, user=None, parsed_start_date=None, parsed_end_date=None):
        campaign = super().save(commit=False)

        # Get the user's organization
        org = user.organization

        campaign.organization = org

        target_url = self.cleaned_data.get('target_url', None)

        if target_url is not None:
            campaign.has_website = True

        regions_list = self.cleaned_data.get('regions_list', None)

        if commit:
            campaign.initial_date = campaign.start_date = parsed_start_date
            campaign.end_date = parsed_end_date
            campaign.save()
            # A campaign needs to have a value for field ”id“
            # before the target_regions many-to-many
            # relationship can be used
            if regions_list is not None:
                for region_name in regions_list.split(','):
                    region = Region.objects.get(name__iexact=region_name.strip())
                    campaign.target_regions.add(region)

        return campaign
