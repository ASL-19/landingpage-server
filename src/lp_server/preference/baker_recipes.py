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

from preference.models import Region, Location


region_iran = Recipe(
    Region,
    name='IRAN')
region_mena = Recipe(
    Region,
    name='MENA')
region_none = Recipe(
    Region,
    name='NONE')

location_us = Recipe(
    Location,
    country='United States',
    city='New York',
    timezone='UTC-5',
    language='English')
location_germany = Recipe(
    Location,
    country='Germany',
    city='Frankfurt',
    timezone='UTC+1',
    language='German')
location_france = Recipe(
    Location,
    country='France',
    city='Paris',
    timezone='UTC+1',
    language='French')
