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

import strawberry
import strawberry_django
from typing import Optional, List

from wagtail.images.models import Image

from lp_server.types.tag import FlatTags
from lp_server.types.generic import GenericScalar
from lp_server.media_storage import get_s3_url


@strawberry.type
class ImageRendition:
    """
    Image rendition object
    """

    id: uuid.UUID
    url: Optional[str]
    width: Optional[int]
    height: Optional[int]


@strawberry.type
class ImageRenditionList:
    """
    A list of Image renditions
    """

    rendition_list: Optional[List[ImageRendition]]

    @strawberry.field
    def src_set(self) -> Optional[str]:
        return ", ".join(
            [f"{img.url} {img.width}w" for img in self.rendition_list])


@strawberry_django.type(Image, pagination=True)
class ImageNode(strawberry.relay.Node):
    """
    Relay: Images node
    """

    id: strawberry.relay.NodeID[int]
    # Define all available image rendition options as arguments
    focal_point_x: Optional[int]
    focal_point_y: Optional[int]
    focal_point_width: Optional[int]
    focal_point_height: Optional[int]
    width: int
    height: int
    file_size: Optional[int]
    file_hash: str
    title: str
    file: str
    created_at: datetime.datetime

    @strawberry.field
    def rendition(
        self,
        max: Optional[str] = strawberry.UNSET,
        min: Optional[str] = strawberry.UNSET,
        width: Optional[int] = strawberry.UNSET,
        height: Optional[int] = strawberry.UNSET,
        fill: Optional[str] = strawberry.UNSET,
        format: Optional[str] = strawberry.UNSET,
        bgcolor: Optional[str] = strawberry.UNSET,
        jpegquality: Optional[int] = strawberry.UNSET
    ) -> Optional[ImageRendition]:
        """
        Filters based on input arguments
        """

        rendition_fields = {}
        if max is not strawberry.UNSET:
            rendition_fields['max'] = max
        if min is not strawberry.UNSET:
            rendition_fields['min'] = min
        if width is not strawberry.UNSET:
            rendition_fields['width'] = width
        if height is not strawberry.UNSET:
            rendition_fields['height'] = height
        if fill is not strawberry.UNSET:
            rendition_fields['fill'] = fill
        if format is not strawberry.UNSET:
            rendition_fields['format'] = format
        if bgcolor is not strawberry.UNSET:
            rendition_fields['bgcolor'] = bgcolor
        if jpegquality is not strawberry.UNSET:
            rendition_fields['jpegquality'] = jpegquality

        filters = "|".join(
            [f"{key}-{val}" for key, val in rendition_fields.items()])

        img = self.get_rendition(filters)
        url = img.url
        s3_url = get_s3_url()
        if s3_url:
            url = url.replace(s3_url, '')

        return ImageRendition(
            id=img.id,
            url=url,
            width=img.width,
            height=img.height)

    @strawberry.field
    def rendition_list(self, sizes: Optional[List[Optional[int]]] = []) -> Optional[ImageRenditionList]:
        """
        Create rendition list based on arguments
        """

        rendition_list = [
            ImageNode.rendition(self, width=width)
            for width in sizes
        ]

        return ImageRenditionList(rendition_list=rendition_list)

    @strawberry.field
    def tags(self) -> Optional[List[Optional[FlatTags]]]:
        return self.tags.all().order_by('slug')


@strawberry.type
class ImageBlock:
    """
    Image block for StreamField
    """

    id: uuid.UUID
    value: Optional[GenericScalar]

    @strawberry.field
    def image(self) -> Optional[ImageNode]:
        return Image.objects.get(id=self.value)


@strawberry.type
class ImageQuery:
    """
    Image Query definition
    """

    @strawberry.field
    def image(self, pk: int) -> Optional[ImageNode]:
        return Image.objects.get(pk=pk)

    images: strawberry.relay.ListConnection[ImageNode] = strawberry_django.connection()
