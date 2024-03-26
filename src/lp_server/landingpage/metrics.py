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

import time
from django.conf import settings
from prometheus_client.metrics import Counter
from prometheus_client import values


class PodCounter(Counter):
    _type = 'counter'

    def _metric_init(self) -> None:
        pod_name = '_' + settings.POD_HOSTNAME
        name = self._type + pod_name
        self._value = values.ValueClass(name, self._name, self._name + '_total', self._labelnames,
                                        self._labelvalues)
        self._created = time.time()


impression_counter = PodCounter(
    'impressions',
    'impressions',
    ['status', 'campaign'])
