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
import time
import uuid

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.html import strip_tags
from gqlauth.core.exceptions import TokenScopeError

from lp_server.constants import TokenAction


def get_token_payload(token, action, exp=None):
    """
    Get the JWT token payload

    Args:
        token (str): A JWT token (JSON string)
        action (str): The action of the token
        exp (optional): The expiry datetime of the
            token. Defaults to None.

    Raises:
        TokenScopeError: if the action is mismatching
            with the payload

    Returns:
        dict: The payload of the JWT token
    """

    payload = signing.loads(token, max_age=exp)
    _action = payload.pop('action')

    if _action != action:
        raise TokenScopeError

    return payload


def using_refresh_tokens():
    """
    Check the JWT token refresh method

    Returns:
        boolean: whether long running
            refresh jwt token method is used
    """

    if (
        hasattr(settings, 'GRAPHQL_JWT') and
        settings.GRAPHQL_JWT.get('JWT_LONG_RUNNING_REFRESH_TOKEN', False) and
        'graphql_jwt.refresh_token.apps.RefreshTokenConfig'
        in settings.INSTALLED_APPS
    ):
        return True
    return False


def revoke_user_refresh_token(user):
    """
    Revoke the user's refresh tokens and update
    their jwt_secret uuid

    Args:
        user (User): A user object
    """
    if using_refresh_tokens():
        # Update the jwt secret of the user on logout,
        # for example, after a password reset
        # to disallow using the password reset token
        # more than once
        user.jwt_secret = uuid.uuid4()
        user.save()

        refresh_tokens = user.refresh_tokens.all()
        for refresh_token in refresh_tokens:
            try:
                refresh_token.revoke()
            except Exception:  # JSONWebTokenError
                pass


def get_user_by_email(email):
    """
    Get a user by email

    raise ObjectDoesNotExist
    """

    UserModel = get_user_model()
    try:
        user = UserModel._default_manager.get(**{UserModel.EMAIL_FIELD: email})
        return user
    except ObjectDoesNotExist:
        return None


def get_token(user, action, **kwargs):
    """
    Get the token for a specific user
    """

    username = user.get_username()
    if hasattr(username, "pk"):
        username = username.pk
    payload = {get_user_model().USERNAME_FIELD: username, "action": action}

    if kwargs:
        payload.update(**kwargs)
    token = signing.dumps(payload)
    return token


def send(subject, template, context, recipient_list=None):
    """
    Sends an email using the django send_mail method

    Args:
        subject (string): The path of the text file
        containing the subject of the email
        template (string): The path of the template of the email
        context (dict): A dict for the email context properties
        recipient_list ([list], optional): a list of email addresses
        to which the email will be sent. Defaults to None.
    """

    _subject = render_to_string(subject, context).replace("\n", " ").strip()
    html_message = render_to_string(template, context)
    message = strip_tags(html_message)

    user = context['user']

    return send_mail(
        subject=_subject,
        from_email=settings.GQL_AUTH.EMAIL_FROM,
        message=message,
        html_message=html_message,
        recipient_list=(
            recipient_list or [getattr(user, get_user_model().EMAIL_FIELD)]
        ),
        fail_silently=False)


def get_email_context(info, path, action, *args, **kwargs):
    """
    Set up email context
    """
    # The request object can either be passed from
    # a mutation resolver (info.context) or directly
    # from a ModelAdmin save
    request = info.context.request if hasattr(info, 'context') else info

    new_user = kwargs.get('new_user', None)

    user = request.user

    if action == TokenAction.PASSWORD_RESET and len(args) > 0:
        user = get_user_by_email(*args[0])  # user email

    token = None
    if new_user is None:
        token = get_token(user, action, **kwargs)

    site = get_current_site(request)

    language = translation.get_language_from_request(
        request, check_path=False)

    return {
        "user": user if new_user is None else new_user,
        "request": request,
        "token": token,
        "port": request.get_port(),
        "site_name": site.name,
        "language": language,
        "domain": site.domain,
        "protocol": "https" if request.is_secure() else "http",
        "path": path,
        "timestamp": time.time(),
        **settings.GQL_AUTH.EMAIL_TEMPLATE_VARIABLES,
    }


def send_invitation_email(info, *args, **kwargs):
    """
    Set up invitation email
    """

    email_context = get_email_context(
        info,
        settings.INVITATION_PATH_ON_EMAIL,
        TokenAction.INVITATION)

    template = settings.EMAIL_TEMPLATE_INVITATION
    subject = settings.EMAIL_SUBJECT_INVITATION

    return send(subject, template, email_context, *args, **kwargs)


def send_new_user_notification_email(info, *args, **kwargs):
    """
    Set up new sign-up notification email
    """

    new_user = kwargs.get('new_user', None)

    email_context = get_email_context(
        info,
        settings.EMAIL_SETTINGS['NEW_USER_NOTIFICATION_PATH_ON_EMAIL'],
        TokenAction.NOTIFICATION,
        new_user=new_user)

    template = settings.EMAIL_SETTINGS['EMAIL_TEMPLATE_NEW_USER']
    subject = settings.EMAIL_SETTINGS['EMAIL_SUBJECT_NEW_USER']

    # Remove the new_user kwarg as the email_context
    # has the respective user object
    kwargs.pop('new_user')

    return send(subject, template, email_context, *args, **kwargs)


def send_new_verification_notification_email(info, *args, **kwargs):
    """
    Set up new verification notification email
    """

    new_user = kwargs.get('new_user', None)

    email_context = get_email_context(
        info,
        settings.EMAIL_SETTINGS['NEW_VERIFICATION_PATH_ON_EMAIL'],
        TokenAction.NOTIFICATION,
        new_user=new_user)

    template = settings.EMAIL_SETTINGS['EMAIL_TEMPLATE_NEW_VERIFICATION']
    subject = settings.EMAIL_SETTINGS['EMAIL_SUBJECT_NEW_VERIFICATION']

    # Remove the new_user kwarg as the email_context
    # has the respective user object
    kwargs.pop('new_user')

    return send(subject, template, email_context, *args, **kwargs)


def get_utc_offset(timezone):
    """
    Get UTC offset from timezone

    Args:
        timezone(string): Timezone pytz format (e.g. 'US/Pacific')
    Returns:
        string: UTC offset (e.g.: '+09:00')
    """

    offset_seconds = datetime.datetime.now(pytz.timezone(timezone)).utcoffset().total_seconds() / 3600
    hours = abs(int(offset_seconds))
    minutes = (offset_seconds * 60) % 60

    if offset_seconds < 0:
        return "-%02d:%02d" % (hours, minutes)
    else:
        return "+%02d:%02d" % (hours, minutes)
