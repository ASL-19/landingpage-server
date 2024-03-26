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

import json
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

from distribution.models import NotificationStatus


def make_keyboard(items, items_per_row=0, add_home=""):
    """
    Makes a keyboard json out of items list and order them per items_per_row.

    :param items: buttons texts list
    :param items_per_row: Number of items per row, if not specified it uses its own algorithm.
    :param add_home: if it should add a back to home button
    :return: keyboard object for use in Telegram API
    """
    keyboard = []
    row = []
    count = 0
    MAX_ITEMS_PER_ROW = 2

    if items_per_row > MAX_ITEMS_PER_ROW or items_per_row < 1:
        items_per_row = MAX_ITEMS_PER_ROW

    for item in items:
        row.append(item)
        count += 1
        if count == items_per_row:
            keyboard.append(list(row))
            row = []
            count = 0

    if len(row) != 0:
        keyboard.append(list(row))

    if add_home != '':
        keyboard.append([add_home])

    return keyboard


def send_telegram(user, chat_id, text, keyboard=[], parse=None):     # noqa C901
    """
    Send a text message to the user

    :param user: vpnuser object
    :param chat_id: ID of the chat with the user
    :param text: text to be sent with the link
    :param keyboard: a compiled keyboard to be sent to the user
    :param parse: Format to parse message in
    :return: Telegram response object
    :raise: TelegramError: Telegram API call failed
    """
    if text is None or len(text) <= 0:
        raise Exception('Text cannot be empty')

    if not settings.TELEGRAM_BOT_TOKEN:
        raise Exception('Telegram Bot Token is not set')

    post_data = {
        'chat_id': chat_id,
        'text': text
    }

    if parse == 'HTML':
        post_data['parse_mode'] = 'HTML'
    elif parse == 'MARKDOWN':
        post_data['parse_mode'] = 'MarkdownV2'

    if len(keyboard) == 0:
        keyboard = make_keyboard([], 1)

    post_data['reply_markup'] = {
        'keyboard': keyboard,
        'one_time_keyboard': False,
        'resize_keyboard': True
    }

    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(json.dumps(post_data)))
    }

    url = f'{settings.TELEGRAM_HOSTNAME}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(post_data))
    except ConnectionError as error:
        raise Exception(f'Error connecting to Telegram API: {str(error)}')
    except HTTPError as error:
        raise Exception(f'Error in POST request to Telegram API: {str(error)}')
    except Timeout as error:
        raise Exception(f'Timeout connecting to Telegram API: {str(error)}')
    if response.status_code >= 400:
        resp_dict = json.loads(response.text)
        # Checking if the bot is blocked by User or the user account is deactivated based on the error description using keywords
        blocked_matches = ["blocked", "BLOCKED", "Blocked"]
        account_deactivation_matches = ["deactivated", "DEACTIVATED", "Deactivated"]
        if resp_dict.get("description", False):
            if any(x in resp_dict["description"] for x in blocked_matches):
                user.notification_status = NotificationStatus.BLOCKED_BOT
            elif any(x in resp_dict["description"] for x in account_deactivation_matches):
                user.notification_status = NotificationStatus.ACCOUNT_DEACTIVATED
            user.save()
        raise Exception(f'Error response from Telegram API: {str(response)} {response.text}')

    return response


def send_email(subject, address, text):
    """
    Send an email to the user

    :param address: Email address of the user
    :param text: text to be sent with the link
    :param context: Context for the email
    """

    if text is None or len(text) <= 0:
        raise Exception('Text (body) cannot be empty')

    subject = subject.replace("\n", " ").strip()
    html_message = text
    message = strip_tags(html_message)

    return send_mail(
        subject=subject,
        from_email=settings.GQL_AUTH.EMAIL_FROM,
        message=message,
        html_message=html_message,
        recipient_list=(
            address,
        ),
        fail_silently=False)
