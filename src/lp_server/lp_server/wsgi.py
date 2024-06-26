# -*- coding: utf-8 -*-
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


import os
from django.core.wsgi import get_wsgi_application

assert 'BUILD_ENV' in os.environ, 'BUILD_ENV not set, don\'t forget to `export BUILD_ENV`'
BUILD_ENV = os.environ['BUILD_ENV']
os.environ['DJANGO_SETTINGS_MODULE'] = 'lp_server.settings.' + BUILD_ENV

application = get_wsgi_application()
