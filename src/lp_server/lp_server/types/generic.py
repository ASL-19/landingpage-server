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

import uuid
import strawberry
from typing import NewType, Any, Optional


GenericScalar = strawberry.scalar(
    NewType("GenericScalar", Any),
    description="The GenericScalar scalar type represents a generic GraphQL scalar value that could be: List or Object."
)


@strawberry.type
class GenericBlock:
    """
    Generic block representation
    """
    id: uuid.UUID
    value: Optional[GenericScalar]


GenericStreamFieldType = strawberry.scalar(
    NewType("GenericStreamFieldType", Any),
    description="",
    serialize=lambda v: v.raw_data,
    parse_value=lambda v: v,
)
