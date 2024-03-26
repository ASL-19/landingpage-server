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

from model_bakery.recipe import Recipe

from server.models import OutlineServer


tg_vpn_server = Recipe(
    OutlineServer,
    name='Telegram Server',
    ipv4='50.60.70.80',
    ipv6='2001:0db8:85a3:0000:0000:8a2e:0370:7334',
    provider='Digital Ocean',
    cost='20',
    user_src='TG',
    reputation=1,
    level=2,
    active=True,
    alert=False,
    is_blocked=False,
    is_distributing=True)

em_vpn_server = Recipe(
    OutlineServer,
    name='Email Server',
    ipv4='60.70.80.90',
    ipv6='2001:0db8:85a3:0000:0000:8a2e:0370:4337',
    provider='AWS',
    cost='10',
    user_src='EM',
    reputation=1,
    level=2,
    active=True,
    alert=False,
    is_blocked=False,
    is_distributing=True)

nn_vpn_server = Recipe(
    OutlineServer,
    name='None Server',
    ipv4='10.20.30.40',
    ipv6='2001:0db8:85a3:0000:0000:8a2e:0370:3333',
    provider='AWS',
    cost='10',
    user_src='EM',
    reputation=1,
    level=2,
    active=True,
    alert=False,
    is_blocked=False,
    is_distributing=True)

em_loc_vpn_server = Recipe(
    OutlineServer,
    name='Email Server',
    ipv4='60.70.80.90',
    ipv6='2001:0db8:85a3:0000:0000:8a2e:0370:4337',
    provider='AWS',
    cost='10',
    user_src='EM',
    reputation=0,
    level=0,
    active=True,
    alert=False,
    is_blocked=False,
    is_distributing=True,
    dist_model=1)

tg_loc_vpn_server = Recipe(
    OutlineServer,
    name='Telegram Server',
    ipv4='60.70.80.91',
    ipv6='2001:0db8:85a3:0000:0000:8a2e:0371:4337',
    provider='AWS',
    cost='10',
    user_src='TG',
    reputation=0,
    level=0,
    active=True,
    alert=False,
    is_blocked=False,
    is_distributing=True,
    dist_model=1)
