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

import random

from django.conf import settings
from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from model_bakery import baker
from rest_framework.test import APITestCase

from accounts.models import Organization, User
from lp_server.schema import schema
from preference.models import Region
from publisher.models import Campaign, Impression

from strawberry.django.context import StrawberryDjangoContext


def anonymous_user_context():
    request = RequestFactory().get('/')
    request.user = AnonymousUser
    return request


def authenticated_user_context():
    User = get_user_model()
    new_user, created = User.objects.get_or_create(username='testuser')
    if created:
        new_user.set_password('testpass')
        new_user.save()
    request = RequestFactory().get('/')
    request.user = new_user
    return request


def authenticated_member_user_context():
    User = get_user_model()
    user = User.objects.get(username='great')
    request = RequestFactory().get('/')
    request.user = user
    return request


class PublisherTests(APITestCase):

    def setUp(self):
        region_iran = baker.make_recipe('preference.region_iran')
        region_mena = baker.make_recipe('preference.region_mena')
        region_none = baker.make_recipe('preference.region_none')

        baker.make_recipe('publisher.great_user')
        baker.make_recipe('publisher.awesome_user')
        baker.make_recipe('publisher.amazing_user')

        organization_group = baker.make_recipe('publisher.organization_group')

        self.great = baker.make_recipe('publisher.great_campaign')
        self.great.target_regions.add(region_mena)
        self.great.target_regions.add(region_iran)
        self.great.save()

        self.awesome = baker.make_recipe('publisher.awesome_campaign')
        self.awesome.target_regions.add(region_iran)
        self.awesome.save()

        self.amazing = baker.make_recipe('publisher.amazing_campaign')
        self.amazing.target_regions.add(region_mena)
        self.amazing.save()

        users = User.objects.filter(
            username__in=['great', 'amazing', 'awesome'])
        for user in users:
            user.groups.add(organization_group)

        self.tg_vpn_server = baker.make_recipe('server.tg_vpn_server')
        self.tg_vpn_server.region.add(region_iran)
        self.tg_vpn_server.region.add(region_mena)
        self.tg_vpn_server.save()

        self.em_vpn_server = baker.make_recipe('server.em_vpn_server')
        self.em_vpn_server.region.add(region_mena)
        self.tg_vpn_server.region.add(region_iran)
        self.em_vpn_server.save()

        self.nn_vpn_server = baker.make_recipe('server.nn_vpn_server')
        self.nn_vpn_server.region.add(region_none)
        self.nn_vpn_server.save()

    def test_objects_created(self):
        self.assertEqual(Region.objects.count(), 3)
        self.assertEqual(Organization.objects.count(), 3)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Campaign.objects.count(), 3)

        great = User.objects.get(username='great')
        self.assertIsNotNone(great)
        great_organization = Organization.objects.get(name=great.organization.name)
        self.assertIsNotNone(great_organization)
        self.assertEqual(str(great_organization), great_organization.name)
        great_campaign = Campaign.objects.get(organization=great_organization)
        self.assertIsNotNone(great_campaign)

        awesome = User.objects.get(username='awesome')
        self.assertIsNotNone(awesome)
        awesome_organization = Organization.objects.get(name=awesome.organization.name)
        self.assertEqual(str(awesome_organization), awesome_organization.name)
        self.assertIsNotNone(awesome_organization)
        awesome_campaign = Campaign.objects.get(organization=awesome_organization)
        self.assertIsNotNone(awesome_campaign)

        amazing = User.objects.get(username='amazing')
        self.assertIsNotNone(amazing)
        amazing_organization = Organization.objects.get(name=amazing.organization.name)
        self.assertEqual(str(amazing_organization), amazing_organization.name)
        self.assertIsNotNone(amazing_organization)
        amazing_campaign = Campaign.objects.get(organization=amazing_organization)
        self.assertIsNotNone(amazing_campaign)

    def test_impressions_created(self):
        great_impressions = Impression.objects.filter(campaign=self.great)
        self.assertEqual(great_impressions.count(), 31)

        awesome_impressions = Impression.objects.filter(campaign=self.awesome)
        self.assertEqual(awesome_impressions.count(), 16)

        amazing_impressions = Impression.objects.filter(campaign=self.amazing)
        self.assertEqual(amazing_impressions.count(), 61)

    def test_landing_page_name(self):
        self.assertEqual(self.great.landing_page,
                         settings.UTM_URL_TEMPLATE.format(
                             url=self.great.target_url,
                             source=self.great.source,
                             name=self.great.name,
                             medium=self.great.medium))
        self.assertEqual(self.awesome.landing_page,
                         settings.UTM_URL_TEMPLATE.format(
                             url=self.awesome.target_url,
                             source=self.awesome.source,
                             name=self.awesome.name,
                             medium=self.awesome.medium))
        self.assertEqual(self.amazing.landing_page,
                         settings.UTM_URL_TEMPLATE.format(
                             url=self.amazing.target_url,
                             source=self.amazing.source,
                             name=self.amazing.name,
                             medium=self.amazing.medium))

    def test_impression_percentage(self):
        impressions = Impression.objects.all()

        sum_per_day = {}
        sum_per_campaign = {}
        for imp in impressions:
            if imp.date in sum_per_day:
                sum_per_day[imp.date]['percentage'] += imp.percentage
                sum_per_day[imp.date]['impressions'] += imp.desired
                sum_per_day[imp.date]['campaigns'][imp.campaign.pk] = {
                    'impressions': imp.desired,
                    'percentage': imp.percentage
                }
            else:
                sum_per_day[imp.date] = {
                    'percentage': imp.percentage,
                    'impressions': imp.desired,
                    'campaigns': {
                        imp.campaign.pk: {
                            'impressions': imp.desired,
                            'percentage': imp.percentage
                        }
                    }
                }

            if imp.campaign.pk in sum_per_campaign:
                sum_per_campaign[imp.campaign.pk] += imp.desired
            else:
                sum_per_campaign[imp.campaign.pk] = imp.desired

        for _, value in sum_per_day.items():
            self.assertLessEqual(abs(value['percentage'] - 100), 1)
            for _, camp in value['campaigns'].items():
                percentage = round(100 * camp['impressions'] / value['impressions'])
                self.assertLessEqual(percentage, camp['percentage'])

        for key, value in sum_per_campaign.items():
            campaign = Campaign.objects.get(pk=key)
            self.assertIsNotNone(campaign)
            self.assertLessEqual(abs(campaign.impression_per_period - value), 100)

    def test_actual_update(self):
        impressions = Impression.objects.filter(
            campaign=self.great).order_by('date')
        self.assertGreater(impressions.count(), 1)

        today = random.randint(0, impressions.count() - 2)
        today_imp = impressions[today]
        tomorrow_imp = impressions[today + 1]

        desired = tomorrow_imp.desired
        variant = random.randint(-100, 100)
        actual = today_imp.desired + variant
        today_imp.actual = actual
        today_imp.save()
        today_imp.update_tomorrow()
        tomorrow_imp.refresh_from_db()
        self.assertEqual(tomorrow_imp.desired, desired - variant)

    def test_landing_page_response(self):

        if settings.CHECK_FOR_SERVERS:
            response = self.client.get('/')
            self.assertEqual(response.status_code, 444)
            self.assertEqual(bytes.decode(response.content), settings.LP_SERVER_NOT_FOUND)

        response = self.client.get('/', REMOTE_ADDR=self.tg_vpn_server.ipv4)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        response = self.client.get('/', REMOTE_ADDR=self.tg_vpn_server.ipv6)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        response = self.client.get('/', REMOTE_ADDR=self.em_vpn_server.ipv4)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        response = self.client.get('/', REMOTE_ADDR=self.em_vpn_server.ipv6)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.content)

        if settings.CHECK_FOR_SERVERS:
            response = self.client.get('/', REMOTE_ADDR=self.nn_vpn_server.ipv4)
            self.assertEqual(response.status_code, 444)
            self.assertEqual(bytes.decode(response.content), settings.LP_SERVER_FOR_REGION_NOT_FOUND)

            response = self.client.get('/', REMOTE_ADDR=self.nn_vpn_server.ipv6)
            self.assertEqual(response.status_code, 444)
            self.assertEqual(bytes.decode(response.content), settings.LP_SERVER_FOR_REGION_NOT_FOUND)

    def test_landing_page_percentage(self):
        """
        Checks the percentage to 10%
        """

        resps = {}
        for i in range(1000):
            response = self.client.get('/', REMOTE_ADDR=self.tg_vpn_server.ipv4)
            key = bytes.decode(response.content)
            if key in resps:
                resps[key] += 1
            else:
                resps[key] = 1

        impressions = Impression.objects.filter(
            date=timezone.now().date())
        for imp in impressions:
            response = imp.campaign.landing_page
            self.assertLessEqual(abs(imp.percentage - resps[response] / 10), 10)


class PublisherGqlAPITests(TestCase):

    def setUp(self):
        region_iran = baker.make_recipe('preference.region_iran')
        region_mena = baker.make_recipe('preference.region_mena')

        self.great_user = baker.make_recipe('publisher.great_user')
        self.great_user.time_zone = 'UTC'
        self.great_user.save()
        self.awesome_user = baker.make_recipe('publisher.awesome_user')
        self.awesome_user.time_zone = 'UTC'
        self.awesome_user.save()
        self.amazing_user = baker.make_recipe('publisher.amazing_user')
        self.amazing_user.time_zone = 'UTC'
        self.amazing_user.save()

        organization_group = baker.make_recipe('publisher.organization_group')

        self.great = baker.make_recipe('publisher.great_campaign')
        self.great.target_regions.add(region_mena)
        self.great.target_regions.add(region_iran)
        self.great.save()

        self.awesome = baker.make_recipe('publisher.awesome_campaign')
        self.awesome.target_regions.add(region_iran)
        self.awesome.save()

        self.amazing = baker.make_recipe('publisher.amazing_campaign')
        self.amazing.target_regions.add(region_mena)
        self.amazing.save()

        users = User.objects.filter(
            username__in=['great', 'amazing', 'awesome'])
        for user in users:
            user.status.verified = True
            user.status.save()
            user.role = 'SU'
            user.save()
            user.groups.add(organization_group)

        self.anonymous_context_value = StrawberryDjangoContext(
            request=anonymous_user_context(),
            response=None)

        self.authenticated_context_value = StrawberryDjangoContext(
            request=authenticated_user_context(),
            response=None)

        self.campaigns_query = """
            {
            campaign(uniqueId: "awesome_campaign") {
                id
                uniqueId
                startDate
                endDate
                totalImpressions(kind: "day", startDate: "1970-01-01", endDate: "2050-01-01") {
                date
                totalImpressions
                totalSpending
                }
            }
            campaigns(
                filters: {approved: true, enabled: true, removed: false}
                orderBy: "start_date"
            ) {
                totalCount
                edges {
                node {
                    uniqueId
                    startDate
                    endDate
                    totalImpressions(kind: "day", startDate: "1970-01-01", endDate: "2050-01-01") {
                    date
                    totalImpressions
                    totalSpending
                    }
                }
                }
            }
            }
        """

        self.create_campaign = """
            mutation {
            createCampaign(
                name: "New Campaign",
                uniqueId: "new-campaign",
                source: "source",
                medium: "medium",
                regionsList: "iran",
                planType: MONTHLY,
                startDate: "2050-01-01",
                impressionPerPeriod: 20
            ) {
                success
                errors
            }
        }
        """

        self.duplicate_campaign = """
            mutation {
            duplicateCampaign(
                newName: "Duplicated Campaign",
                originalCampaignUniqueId: "great_campaign1",
                newStartDate: "2050-01-01",
                newEndDate: "2050-02-01"
            ) {
                success
                errors
            }
        }
        """

        self.delete_non_existing_campaigns = """
            mutation {
            deleteCampaign(
                campaignUniqueIds: ["great_campaign1", "awesome"],
            ) {
                success
                errors
            }
        }
        """

        self.delete_existing_campaigns = """
            mutation {
            deleteCampaign(
                campaignUniqueIds: ["great_campaign1", "awesome_campaign3"],
            ) {
                success
                errors
            }
        }
        """

        self.delete_campaign = """
            mutation {
            deleteCampaign(
                campaignUniqueIds: ["great_campaign1"],
            ) {
                success
                errors
            }
        }
        """

        self.enable_campaign = """
            mutation {
            enableCampaign(
                campaignUniqueId: "great_campaign1",
            ) {
                success
                errors
            }
        }
        """

        self.disable_campaign = """
            mutation {
            disableCampaign(
                campaignUniqueId: "great_campaign1",
            ) {
                success
                errors
            }
        }
        """

    def test_get_campaigns(self):
        """
        Getting campaigns request
        """

        # User not a member of any org
        response = schema.execute_sync(
            self.campaigns_query,
            context_value=self.authenticated_context_value)
        assert response.errors is None
        assert response.data['campaign'] is None
        assert response.data['campaigns']['totalCount'] == 0
        assert response.data['campaigns']['edges'] == []

        # User can access 'great_campaign' only
        response = schema.execute_sync(
            self.campaigns_query,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['campaign'] is None
        assert response.data['campaigns']['totalCount'] == 1
        assert response.data['campaigns']['edges'][0]['node']['uniqueId'] == 'great_campaign1'

    def test_create_campaign(self):
        """
        Creating campaign request
        """

        # Anonymous user request
        response = schema.execute_sync(
            self.create_campaign,
            context_value=self.anonymous_context_value)
        assert response.errors is None
        assert response.data['createCampaign']['success'] is False
        assert response.data['createCampaign']['errors']['nonFieldErrors'][0]['code'] == 'unauthenticated'

        # User of org 'great_org' request
        response = schema.execute_sync(
            self.create_campaign,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['createCampaign']['success'] is True
        assert response.data['createCampaign']['errors'] is None

        campaign = Campaign.objects.get(unique_id='new-campaign')
        campaign.enabled = True
        campaign.approved = True
        campaign.save()
        response = schema.execute_sync(
            self.campaigns_query,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['campaign'] is None
        assert response.data['campaigns']['totalCount'] == 2
        assert response.data['campaigns']['edges'][0]['node']['uniqueId'] == 'great_campaign1'
        assert response.data['campaigns']['edges'][1]['node']['uniqueId'] == 'new-campaign'

    def test_duplicate_campaign(self):
        """
        Duplicating campaign request
        """

        # Authenticated user not member of org request
        response = schema.execute_sync(
            self.duplicate_campaign,
            context_value=self.authenticated_context_value)
        assert response.errors is None
        assert response.data['duplicateCampaign']['success'] is False
        assert response.data['duplicateCampaign']['errors']['nonFieldErrors'][0]['code'] == 'no_organization'

        # User of org 'great_org' request
        response = schema.execute_sync(
            self.duplicate_campaign,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['duplicateCampaign']['success'] is True
        assert response.data['duplicateCampaign']['errors'] is None

        campaign = Campaign.objects.get(name='Duplicated Campaign')
        campaign.enabled = True
        campaign.approved = True
        campaign.save()
        response = schema.execute_sync(
            self.campaigns_query,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['campaign'] is None
        assert response.data['campaigns']['totalCount'] == 2
        assert response.data['campaigns']['edges'][0]['node']['uniqueId'] == 'great_campaign1'
        assert response.data['campaigns']['edges'][1]['node']['uniqueId'] == 'great_campaign1-copy1'

    def test_enable_disable_delete_campaign(self):
        """
        Deleting campaign request
        """

        # Authenticated user not member of org request
        response = schema.execute_sync(
            self.delete_campaign,
            context_value=self.authenticated_context_value)
        assert response.errors is None
        assert response.data['deleteCampaign']['success'] is False
        assert response.data['deleteCampaign']['errors']['nonFieldErrors'][0]['code'] == 'no_organization'

        # User of org 'great_org' request: disable campaign
        response = schema.execute_sync(
            self.disable_campaign,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['disableCampaign']['success'] is True
        assert response.data['disableCampaign']['errors'] is None

        # User of org 'great_org' request: enable campaign
        response = schema.execute_sync(
            self.enable_campaign,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['enableCampaign']['success'] is True
        assert response.data['enableCampaign']['errors'] is None

        # User of org 'great_org' request: delete enabled campaign
        response = schema.execute_sync(
            self.delete_campaign,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['deleteCampaign']['success'] is False
        assert response.data['deleteCampaign']['errors']['nonFieldErrors'][0]['code'] == 'campaign_not_disabled'

        # User of org 'great_org' request: delete disabled campaign
        campaign = self.great
        campaign.enabled = False
        campaign.save()

        response = schema.execute_sync(  # Sending a non existing campaign with own campaign
            self.delete_non_existing_campaigns,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['deleteCampaign']['success'] is False
        assert response.data['deleteCampaign']['errors']['nonFieldErrors'][0]['code'] == 'campaign_deletion_error'

        response = schema.execute_sync(  # Sending another org's campaign with own campaign
            self.delete_existing_campaigns,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['deleteCampaign']['success'] is False
        assert response.data['deleteCampaign']['errors']['nonFieldErrors'][0]['code'] == 'organization_not_matching'

        response = schema.execute_sync(
            self.delete_campaign,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['deleteCampaign']['success'] is True
        assert response.data['deleteCampaign']['errors'] is None

        response = schema.execute_sync(
            self.campaigns_query,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['campaign'] is None
        assert response.data['campaigns']['totalCount'] == 0

        # User of org 'great_org' request: delete removed campaign
        response = schema.execute_sync(
            self.delete_campaign,
            context_value=StrawberryDjangoContext(
                request=authenticated_member_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['deleteCampaign']['success'] is False
        assert response.data['deleteCampaign']['errors']['nonFieldErrors'][0]['code'] == 'campaign_already_removed'
