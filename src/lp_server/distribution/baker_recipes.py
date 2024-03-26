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
from distribution.models import Vpnuser, OutlineUser


vpnuser = Recipe(
    Vpnuser,
    reputation=0,
    delete_date=None,
    banned=False,
)

outlineuser = Recipe(
    OutlineUser,
    reputation=0,
    active=True,
    removed=False,
    group_id=None,
)
