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

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

from lp_server.constants import TokenAction

from .utils import send, get_email_context


class Role(models.TextChoices):
    SUPERVISOR = 'SU', _('SUPERVISOR')
    VIEWER = 'VI', _('VIEWER')


class Currency(models.TextChoices):
    CAD = 'CAD', _('CAD')
    IRR = 'IRR', _('IRR')
    USD = 'USD', _('USD')
    EUR = 'EUR', _('EUR')


class Organization(models.Model):
    """
    A model to define organizations
    """

    name = models.CharField(
        _('name'),
        max_length=128,
        unique=True,
        blank=True,
        help_text=_('The name of organization'))

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    A custom user model based on the default django user model
    """

    import pytz
    TIME_ZONE_CHOICES = list(zip(pytz.common_timezones, pytz.common_timezones))

    email = models.EmailField(_('email address'), blank=False, null=False, unique=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='users',
        null=True,
        blank=True)
    role = models.CharField(
        _('role'),
        max_length=2,
        choices=Role.choices,
        default=Role.VIEWER)
    time_zone = models.CharField(
        _('time zone'),
        choices=TIME_ZONE_CHOICES,
        default='UTC',
        max_length=64,
        help_text=_('The timezone where the user resides in'))
    currency = models.CharField(
        _('currency'),
        choices=Currency.choices,
        default=Currency.CAD,
        max_length=3,
        help_text=_('The currency of any budget the user may view'))
    invited = models.BooleanField(
        _('invited'),
        default=False,
        editable=False)
    # Used in the password reset JWT token
    jwt_secret = models.UUIDField(
        default=uuid.uuid4,
        editable=False)
    monitoring_access = models.BooleanField(
        default=False)

    def send_password_reset_email(self, info, *args, **kwargs):
        """
        Send a new password reset email
        """

        email_context = get_email_context(
            info,
            settings.GQL_AUTH.PASSWORD_RESET_PATH_ON_EMAIL,
            TokenAction.PASSWORD_RESET,
            *args,
            **kwargs)

        if 'jwt_secret' in kwargs:
            # Pop the secret kwarg as we no longer need it
            # for send() below
            kwargs.pop('jwt_secret')

        template = settings.GQL_AUTH.EMAIL_TEMPLATE_PASSWORD_RESET
        subject = settings.GQL_AUTH.EMAIL_SUBJECT_PASSWORD_RESET
        return send(subject, template, email_context, *args, **kwargs)


class Invitation(models.Model):
    """
    A model to define the user invites
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invites')
    first_name = models.CharField(
        _('invitee first name'),
        max_length=150,
        blank=True)
    last_name = models.CharField(
        _('invitee last name'),
        max_length=150,
        blank=True)
    email = models.EmailField(
        _('invitee email address'),
        unique=True,
        max_length=254)
    role = models.CharField(
        _('role'),
        max_length=2,
        choices=Role.choices,
        default=Role.VIEWER)
    accepted = models.BooleanField(
        _('accepted'),
        default=False)
    created = models.DateTimeField(
        _('created'),
        default=timezone.now)

    def __str__(self):
        return f'Invitation: {self.email}'
