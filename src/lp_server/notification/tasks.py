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

from celery.utils.log import get_task_logger

from lp_server.celery import app
from notification.models import NotificationBroadcast
from distribution.models import Vpnuser

logger = get_task_logger(__name__)


@app.task()
def add_broadcast_recipients_task(broadcast_id, user_ids):
    """
    Add the given recipients (vpn users) to the given broadcast

    Args:
        broadcast_id (int): The id of the broadcast
        user_ids (list): A list of user ids
    """

    broadcast = NotificationBroadcast.objects.get(id=broadcast_id)
    recipients = Vpnuser.objects.filter(id__in=user_ids)

    logger.info('Adding recipients..')
    for user in recipients:
        broadcast.recipients.add(user)
    logger.info('All recipients were added!')
