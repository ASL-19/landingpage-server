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

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from accounts.models import Organization, User
from lp_server.schema import schema

from strawberry.django.context import StrawberryDjangoContext


def anonymous_user_context():
    request = RequestFactory().get('/')
    request.user = AnonymousUser
    return request


def authenticated_user_context():
    User = get_user_model()
    try:
        new_user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        new_user = AnonymousUser
    request = RequestFactory().get('/')
    request.user = new_user
    return request


class AccountsGqlAPITests(TestCase):

    def setUp(self):

        self.anonymous_context_value = StrawberryDjangoContext(
            request=anonymous_user_context(),
            response=None)

        self.refresh_token = """
            mutation($token: String!) {
                refreshToken(refreshToken: $token, revokeRefreshToken: false) {
                    errors
                    refreshToken {
                    token
                    }
                    success
                    token {
                    token
                    }
                }
            }
        """

        self.token_auth = """
            mutation {
                tokenAuth(username: "testuser", password: "testp@ass_123") {
                    refreshToken {
                        token
                    }
                    user {
                        username
                    }
                    success
                    errors
                }
                }
        """

        self.update_time_zone = """
            mutation {
                updateAccount(
                    timeZone: {
                        displayName: "US/Pacific",
                        utc: "-07:00"
                    }
                ) {
                    success
                    errors
                }
            }
        """

        self.update_currency = """
            mutation {
                updateAccount(
                    currency: EUR
                ) {
                    success
                    errors
                }
            }
        """

        self.update_name = """
            mutation {
                updateAccount(
                    firstName: "First"
                    lastName: "Last"
                ) {
                    success
                    errors
                }
            }
        """

        self.sign_up = """
            mutation {
                signUp(
                    email: "user@example.com"
                    firstName: "Ufirst"
                    lastName: "Ulast"
                    org: "Org Name"
                    password1: "testp@ass_123"
                    password2: "testp@ass_123"
                    username: "testuser"
                ) {
                    success
                    errors
                }
            }
        """

        self.send_password_reset_email = """
            mutation {
                sendPasswordResetEmail(email: "user@example.com") {
                    errors
                    success
                }
            }
        """

        self.password_reset = """
            mutation($token: String!) {
                passwordReset(
                    newPassword1: "testnewpass"
                    newPassword2: "testnewpass"
                    token: $token
                ) {
                    errors
                    success
                }
            }
        """

        self.invite_member = """
            mutation {
                inviteMember(
                firstName: "Ifirst"
                lastName: "Ilast"
                email: "invited_user@example.com"
                role: VIEWER
                ) {
                    success
                    errors
                }
            }
        """

        self.update_team_member_role = """
            mutation($pk: Int!) {
                updateTeamMemberRole(role: SUPERVISOR, userId: $pk) {
                    success
                    errors
                }
            }
        """

        self.get_logged_in_user = """
            {
                me {
                    username
                    timeZone
                    currency
                    firstName
                    lastName
                    organization {
                        name
                        users {
                            edges {
                                node {
                                    username
                                    role
                                }
                            }
                        }
                    }
                }
            }
        """

    def test_accounts_mutations(self):
        """
        Getting campaigns request
        """

        # Signing up 'testuser' signed up
        response = schema.execute_sync(
            self.sign_up,
            context_value=self.anonymous_context_value)
        assert response.errors is None
        assert response.data['signUp']['success'] is True
        assert response.data['signUp']['errors'] is None

        # Updating account timezone (anonymous request)
        response = schema.execute_sync(
            self.update_time_zone,
            context_value=self.anonymous_context_value)
        assert response.errors is None
        assert response.data['updateAccount']['success'] is False
        assert response.data['updateAccount']['errors']['nonFieldErrors'][0]['code'] == 'unauthenticated'

        # Updating account timezone (authenticated request - unverified)
        response = schema.execute_sync(
            self.update_time_zone,
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['updateAccount']['success'] is False
        assert response.data['updateAccount']['errors']['nonFieldErrors'][0]['code'] == 'not_verified'

        # Updating account timezone (authenticated request - verified)
        user = User.objects.get(username='testuser')
        user.status.verified = True
        user.status.save()
        response = schema.execute_sync(
            self.update_time_zone,
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['updateAccount']['success'] is True
        assert response.data['updateAccount']['errors'] is None

        # Updating account currency (authenticated request - verified)
        response = schema.execute_sync(
            self.update_currency,
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['updateAccount']['success'] is True
        assert response.data['updateAccount']['errors'] is None

        # Updating account name (authenticated request - verified)
        response = schema.execute_sync(
            self.update_name,
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['updateAccount']['success'] is True
        assert response.data['updateAccount']['errors'] is None

        # Changing member role
        viewer = User.objects.create(username='vieweruser')
        viewer.set_password('viewerp@ss_123')
        viewer.organization = Organization.objects.get(name='Org Name')
        viewer.role = 'VI'
        viewer.save()
        response = schema.execute_sync(
            self.update_team_member_role,
            variable_values={
                'pk': viewer.pk
            },
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['updateTeamMemberRole']['success'] is True
        assert response.data['updateTeamMemberRole']['errors'] is None

        # Calling me query and making sure all values were updated
        response = schema.execute_sync(
            self.get_logged_in_user,
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['me']['username'] == 'testuser'
        assert response.data['me']['firstName'] == 'First'
        assert response.data['me']['lastName'] == 'Last'
        assert response.data['me']['currency'] == 'EUR'
        assert response.data['me']['timeZone']['displayName'] == 'US/Pacific'
        assert response.data['me']['organization']['users']['edges'] == [
            {
                'node': {'username': 'vieweruser', 'role': 'SUPERVISOR'}
            },
            {
                'node': {'username': 'testuser', 'role': 'SUPERVISOR'}
            }
        ]

        # Logging in
        response = schema.execute_sync(
            self.token_auth,
            context_value=self.anonymous_context_value
        )
        assert response.errors is None
        assert response.data['tokenAuth']['success'] is True
        assert response.data['tokenAuth']['errors'] is None
        assert response.data['tokenAuth']['user']['username'] == 'testuser'
        refresh_token = response.data['tokenAuth']['refreshToken']['token']

        # Refresh token
        response = schema.execute_sync(
            self.refresh_token,
            variable_values={
                'token': refresh_token
            },
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['refreshToken']['success'] is True
        assert response.data['refreshToken']['errors'] is None

        # Inviting new member
        response = schema.execute_sync(
            self.invite_member,
            context_value=StrawberryDjangoContext(
                request=authenticated_user_context(),
                response=None
            )
        )
        assert response.errors is None
        assert response.data['inviteMember']['success'] is True
        assert response.data['inviteMember']['errors'] is None
