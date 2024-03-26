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
from strawberry.scalars import JSON

from typing import NewType


def serialize(value):
    return (
        {
            'name': value.name,
            'slug': value.slug
        }
    )


FlatTags = strawberry.scalar(
    NewType("FlatTags", JSON),
    description="",
    serialize=lambda v: serialize(v),
    parse_value=lambda v: v,
)
