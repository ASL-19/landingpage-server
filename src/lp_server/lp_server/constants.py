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

from django.utils.translation import gettext as _


class Messages:

    # accounts errors
    UNAUTHENTICATED = [{
        'message': _('Unauthenticated.'),
        'code': 'unauthenticated'}]
    NO_ORGANIZATION = [{
        'message': _('Your account has not been associated with an organization yet.'),
        'code': 'no_organization'}]
    EMAIL_FAIL = [{
        'message': _('Failed to send email.'),
        'code': 'email_fail'}]
    NOT_VERIFIED = [{
        'message': _('Your account has not been verified yet.'),
        'code': 'not_verified'}]
    NOT_SUPERVISOR = [{
        'message': _('Your account is not an admin account.'),
        'code': 'not_supervisor'}]
    USER_NOT_FOUND = [{
        'message': _('The specified user does not exist in your organization.'),
        'code': 'user_not_found'}]
    NO_UPDATE_ARGS = [{
        'message': _('You have to provide at least one account property to update.'),
        'code': 'no_args'}]
    INVALID_TIMEZONE = [{
        'message': _('Please provide a valid time zone.'),
        'code': 'invalid_value'}]
    INVALID_TOKEN = [{
        'message': _('The link or token is invalid.'),
        'code': 'invalid_token'}]
    EXPIRED_TOKEN = [{
        'message': _('The link or token is expired.'),
        'code': 'expired_token'}]
    NOT_VERIFIED_PASSWORD_RESET = [{
        'message': _('The user account is not verified.'),
        'code': 'user_not_verified'}]
    DOWNGRADE_OWN_ROLE_PROHIBITED = [{
        'message': _('Supervisors cannot downgrade their current role at this time.'),
        'code': 'prohibited'}]

    # publisher errors
    MISSING_END_DATE = [{
        'message': _('An end date is required for a one-time campaign.'),
        'code': 'missing_end_date'}]
    END_DATE_PROVIDED = [{
        'message': _('A monthly campaign must not have an end date.'),
        'code': 'end_date_provided'}]
    START_DATE_PRECEDING_TODAY = [{
        'message': _('The start date cannot precede the date of today.'),
        'code': 'start_date_error'}]
    END_DATE_PRECEDING_START_DATE = [{
        'message': _('The end date cannot precede the start date.'),
        'code': 'end_date_error'}]
    CAMPAIGN_NOT_DISABLED = [{
        'message': _('The specified campaign has to be disabled (paused) before the deletion.'),
        'code': 'campaign_not_disabled'}]
    CAMPAIGN_AlREADY_REMOVED = [{
        'message': _('The specified campaign is removed!'),
        'code': 'campaign_already_removed'}]
    CAMPAIGN_NOT_APPROVED = [{
        'message': _('The specified campaign is not approved!'),
        'code': 'campaign_not_approved'}]
    CAMPAIGN_ALREADY_ENABLED = [{
        'message': _('The specified campaign is already enabled!'),
        'code': 'campaign_already_enabled'}]
    CAMPAIGN_ALREADY_DISABLED = [{
        'message': _('The specified campaign is already disabled!'),
        'code': 'campaign_already_disabled'}]
    ORGANIZATION_NOT_MATCHING = [{
        'message': _('The current organization is not matching the organization of the campaign.'),
        'code': 'organization_not_matching'}]
    UNIQUE_ID_USED = [{
        'message': _('The specified unique Identifier (Unique Id) had been used before.'),
        'code': 'unique_id_used'}]


class TokenAction(object):
    INVITATION = 'invitation'
    NOTIFICATION = 'notification'
    PASSWORD_RESET = 'password_reset'
