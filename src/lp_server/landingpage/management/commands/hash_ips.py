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

import re
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from landingpage.models import RequestsHistory
from landingpage.utils import hashit, clean_headers


class Command(BaseCommand):
    help = 'Hashes the IP addresses in the Request History rows'

    def jsonvalue(self, text):
        try:
            headers = json.loads(text)
        except json.decoder.JSONDecodeError:
            return {}, True
        return headers, False

    def hash_ip(self, value):
        ippattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if settings.IPADDRESS_OBFUSCATE == 'HASH':
            if re.match(ippattern, value):
                value = hashit(value)
                changed = True
        else:
            if value != '':
                value = hashit(value)
                changed = True

        return value, changed

    def handle(self, *args, **options):
        self.stderr.write('The command is disabled')
        return
        changed = False
        modified = 0

        qs = RequestsHistory.objects.all().order_by('id')
        paginator = Paginator(qs, 2000)
        num_pages = paginator.num_pages

        for page in range(1, num_pages + 1):
            self.stdout.write(f'Page {page} out of {num_pages}')

            for req in paginator.page(page).object_list:
                if req.ip_address:
                    req.ip_address, changed = self.hash_ip(req.ip_address)
                if req.ip_address_fwd:
                    req.ip_address_fwd, changed = self.hash_ip(req.ip_address_fwd)

                headers, erred = self.jsonvalue(req.headers)
                if type(headers) == str:
                    headers = headers.replace('\'', '\"')
                    headers, erred = self.jsonvalue(headers)
                if type(headers) != dict:
                    self.stderr.write(f'Unable to convert record {req.id}')
                    continue
                req.headers, h_changed = clean_headers(headers)
                if changed or h_changed or erred:
                    modified += 1
                    req.save()

        self.stdout.write(f'Modified {modified} record(s)')
