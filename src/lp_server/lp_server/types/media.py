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
import datetime
import mimetypes

import strawberry
import strawberry_django

from typing import Optional, List

from wagtailmedia.models import Media

from lp_server.types.tag import FlatTags
from lp_server.types.generic import GenericScalar
from lp_server.media_storage import get_s3_url


@strawberry_django.type(Media, pagination=True)
class MediaNode(strawberry.relay.Node):
    """
    Media Node
    """

    id: strawberry.relay.NodeID[int]
    url: Optional[str]
    file_type: Optional[str]
    content_type: Optional[str]
    file_hash: str
    title: str
    file: str
    type: str
    height: strawberry.auto
    width: strawberry.auto
    duration: strawberry.auto
    thumbnail: str
    created_at: datetime.datetime

    @strawberry.field
    def url(self) -> str:
        url = self.url
        s3_url = get_s3_url()
        if s3_url:
            url = url.replace(s3_url, '')

        return url

    @strawberry.field
    def file_type(self) -> str:
        return self.file.name.split('.')[-1].lower()

    @strawberry.field
    def content_type(self) -> str:
        return mimetypes.guess_type(self.file.name)[0]

    @strawberry.field
    def tags(self) -> Optional[List[Optional[FlatTags]]]:
        return self.tags.all().order_by('slug')


@strawberry.type
class MediaBlock:
    """
    Media block for StreamField
    """

    id: uuid.UUID
    value: Optional[GenericScalar]

    @strawberry.field
    def media(self) -> Optional[MediaNode]:
        return Media.objects.get(id=self.value)


@strawberry.type
class MediaQuery:
    """
    Media Query definition
    """

    @strawberry.field
    def media(self, pk: int) -> Optional[MediaNode]:
        return Media.objects.get(pk=pk)

    medias: strawberry.relay.ListConnection[MediaNode] = strawberry_django.connection()
