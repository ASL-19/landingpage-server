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

import datetime
from typing import Iterable, List, Optional

import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginationInput
from wagtail.models import Page

from blog.schema import HeadingBlock, ParagraphBlock
from lp_server.types.document import DocumentBlock
from lp_server.types.generic import GenericBlock, GenericScalar
from lp_server.types.image import ImageBlock, ImageNode
from lp_server.types.media import MediaBlock
from publisher.schema import Connection
from static_page.models import StaticPage, StaticPageFaqRelationship


@strawberry.type
class LinkBlock(GenericBlock):
    pass


@strawberry.type
class EmailBlock(GenericBlock):
    pass


@strawberry.django.filters.filter(StaticPageFaqRelationship, lookups=True)
class StaticPageFaqFilter:
    id: strawberry.relay.NodeID[int]
    faq: strawberry.auto


@strawberry_django.type(StaticPageFaqRelationship, pagination=True, filters=StaticPageFaqFilter)
class StaticPageFaqNode(strawberry.relay.Node):
    """
    Relay: StaticPage Faq Node
    """

    @strawberry.field
    def question(self) -> Optional[str]:
        return self.faq.question

    @strawberry.field
    def answer(self) -> Optional[str]:
        return self.faq.answer


@strawberry.django.filters.filter(StaticPage, lookups=True)
class StaticPageFilter:
    title: strawberry.auto
    published: strawberry.auto
    slug: strawberry.auto


@strawberry_django.type(StaticPage, pagination=True, filters=StaticPageFilter)
class StaticPageNode(strawberry.relay.Node):
    """
    Relay: Static Page Node
    """

    id: strawberry.relay.NodeID[int]
    title: str
    slug: str
    numchild: int
    url_path: str
    seo_title: str
    search_description: str
    published: datetime.date
    image: Optional[ImageNode]

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.live()

    @strawberry.field
    def faqs(self) -> Optional[List[Optional[StaticPageFaqNode]]]:
        return self.faqs.all()

    @strawberry.field
    def body(self) -> Optional[  # noqa C901
        List[
            strawberry.union(
                'StaticPageBody',
                (
                    ParagraphBlock,
                    HeadingBlock,
                    ImageBlock,
                    DocumentBlock,
                    MediaBlock,
                    LinkBlock,
                    EmailBlock,
                )
            )
        ]
    ]:
        """
        Return repr based on block type
        """

        def repr_page(value):
            cls = Page.objects.get(pk=value).specific_class
            if cls == StaticPage:
                return StaticPageBlock(value=value)

            return None

        def repr_others(block_type, value):
            if block_type == 'heading':
                return HeadingBlock(id=id, value=value)
            elif block_type == 'paragraph':
                return ParagraphBlock(id=id, value=value)
            elif block_type == 'image':
                return ImageBlock(id=id, value=value)
            elif block_type == 'document':
                return DocumentBlock(id=id, value=value)
            elif block_type == 'media':
                return MediaBlock(id=id, value=value)
            elif block_type == 'link':
                return LinkBlock(id=id, value=value)
            elif block_type == 'email':
                return EmailBlock(id=id, value=value)

            return None

        repr_body = []
        for block in self.body.raw_data:

            block_type = block.get('type')
            id = block.get('id')
            value = block.get('value')

            if block_type == 'page':
                block = repr_page(value)
                if block is not None:
                    repr_body.append(block)
            else:
                block = repr_others(block_type, value)
                if block is not None:
                    repr_body.append(block)

        return repr_body


@strawberry.type
class StaticPageBlock:
    """
    StaticPage block for StreamField
    """

    value: GenericScalar

    @strawberry.field
    def page(self) -> Optional[StaticPageNode]:
        return StaticPage.objects.get(id=self.value, live=True)


@strawberry.type
class StaticPageQuery:
    """
    Static page Query definition
    """

    @strawberry.field
    def static_page(root, slug: str) -> Optional[StaticPageNode]:
        page = None
        try:
            page = StaticPage.objects.get(
                slug__iexact=slug,
                live=True)
        except StaticPage.DoesNotExist:
            pass

        return page

    @strawberry_django.connection(Connection[StaticPageNode])
    def static_pages(
        self,
        order_by: Optional[List[Optional[str]]] = strawberry.UNSET,
        pagination: Optional[OffsetPaginationInput] = strawberry.UNSET
    ) -> Iterable[StaticPageNode]:
        order = [] if order_by is strawberry.UNSET else order_by
        static_pages = StaticPage.objects.all().order_by(*order)
        return strawberry_django.pagination.apply(pagination, static_pages)
