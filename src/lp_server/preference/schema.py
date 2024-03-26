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

import strawberry
import strawberry_django
from strawberry_django.permissions import IsAuthenticated

from typing import Optional

from preference.models import Region, Faq


@strawberry.django.filters.filter(Region, lookups=True)
class RegionFilter:
    name: strawberry.auto


@strawberry_django.type(Region, pagination=True, filters=RegionFilter)
class RegionNode(strawberry.relay.Node):
    """
    Relay: Region Node
    """

    id: strawberry.relay.NodeID[int]
    name: strawberry.auto


@strawberry.django.filters.filter(Faq, lookups=True)
class FaqFilter:
    question: strawberry.auto
    answer: strawberry.auto


@strawberry_django.type(Faq, pagination=True, filters=RegionFilter)
class FaqNode(strawberry.relay.Node):
    """
    Relay: Faq Node
    """

    id: strawberry.relay.NodeID[int]
    question: strawberry.auto
    answer: strawberry.auto


@strawberry.type
class PreferenceQuery:
    """
    Preference Query definition
    """

    @strawberry.field(extensions=[IsAuthenticated()])
    def region(self, pk: int) -> Optional[RegionNode]:
        return Region.objects.get(pk=pk)

    regions: strawberry.relay.ListConnection[RegionNode] = strawberry_django.connection(extensions=[IsAuthenticated()])

    @strawberry.field(extensions=[IsAuthenticated()])
    def faq(self, pk: int) -> Optional[FaqNode]:
        return Faq.objects.get(pk=pk)

    faqs: strawberry.relay.ListConnection[FaqNode] = strawberry_django.connection(extensions=[IsAuthenticated()])
