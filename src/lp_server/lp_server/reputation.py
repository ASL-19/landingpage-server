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

from django.conf import settings

from reputation.models import ReputationSystemBase


class ReputationSystem(ReputationSystemBase):

    @staticmethod
    def server_level(user_reputation):

        if hasattr(settings, 'REPUTATION_MAP'):
            reputation_map = settings.REPUTATION_MAP
        else:
            reputation_map = [0, 1, 2, 3]

        level = 0
        for n in reversed(range(len(reputation_map))):
            if user_reputation >= reputation_map[n]:
                level = n
                break

        return level

    @staticmethod
    def after_new_key(curr_rep):
        """
            This method increases the user's reputation by 1 after each request
        """

        return curr_rep + 1
