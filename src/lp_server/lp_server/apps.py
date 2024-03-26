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

import sys
from django.apps import AppConfig

from .cloudfront import register_request_cloudfront_invalidation_signal_handlers


class MainConfig(AppConfig):
    name = 'lp_server'
    verbose_name = 'Landing Page Server App'

    has_run = False

    def ready(self):
        """
        Runs once when app is initialized.
        https://stackoverflow.com/a/16111968/7949868
        """
        from lp_server.utils import unregister_prometheus_metrics
        unregister_prometheus_metrics()

        if 'test' not in sys.argv:
            register_request_cloudfront_invalidation_signal_handlers()
