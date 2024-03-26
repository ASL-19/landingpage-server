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
from typing import TYPE_CHECKING, Annotated, Iterable, List, Optional

import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginationInput
from strawberry_django.permissions import IsAuthenticated
from wagtail.models import Page

from blog.models import BlogIndexPage, PostPage
from lp_server.types.document import DocumentBlock
from lp_server.types.generic import GenericBlock, GenericScalar
from lp_server.types.image import ImageBlock, ImageNode
from lp_server.types.media import MediaBlock
from lp_server.types.richtext import RichTextFieldType
from lp_server.types.tag import FlatTags
from publisher.schema import Connection


@strawberry.type
class HeadingBlock(GenericBlock):
    """
    Heading block for StreamField
    """

    pass


@strawberry.type
class ParagraphBlock(GenericBlock):
    """
    Paragraph block for StreamField
    """

    @strawberry.field
    def html(self) -> Optional[RichTextFieldType]:
        return self.value


@strawberry.type
class CollapsibleBlock(GenericBlock):

    @strawberry.field
    def html(self) -> Optional[RichTextFieldType]:
        return self.value


@strawberry.type
class RelatedPostBlock:
    """
    Related Post block for StreamField
    """
    if TYPE_CHECKING:
        from blog.schema import PostNode

    value: GenericScalar

    @strawberry.field
    def related_posts(self) -> Optional[List[Optional[Annotated['PostNode', strawberry.lazy('blog.schema')]]]]:
        related_post_ids = []
        for post in self.value:
            related_post_ids.append(post['value'])
        return PostPage.objects.filter(id__in=related_post_ids).live()


@strawberry.django.filters.filter(PostPage, lookups=True)
class BlogFilter:
    title: strawberry.auto
    published: strawberry.auto
    slug: strawberry.auto
    tags: strawberry.auto


@strawberry_django.type(PostPage, pagination=True, filters=BlogFilter)
class PostNode(strawberry.relay.Node):
    """
    Relay: Blog Post Page Node
    """

    id: strawberry.relay.NodeID[int]
    title: str
    slug: str
    numchild: int
    url_path: str
    seo_title: str
    search_description: str
    published: datetime.date
    read_time: Optional[float]
    synopsis: Optional[str]
    summary: Optional[str]
    featured_image: Optional[ImageNode]
    featured: strawberry.auto

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.live()

    @strawberry.field
    def body(self) -> Optional[  # noqa C901
        List[
            strawberry.union(
                'PostBody',
                (
                    HeadingBlock,
                    ParagraphBlock,
                    ImageBlock,
                    DocumentBlock,
                    MediaBlock,
                    CollapsibleBlock,
                    RelatedPostBlock,
                )
            )
        ]
    ]:
        """
        Return repr based on block type
        """

        def repr_page(value):
            cls = Page.objects.get(pk=value).specific_class
            if cls == PostPage:
                return PostBlock(value=value)

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
            elif block_type == 'collapsible':
                return CollapsibleBlock(id=id, value=value)
            elif block_type == 'related_posts':
                return RelatedPostBlock(id=id, value=value)

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

    @strawberry.field
    def tags(self) -> Optional[List[Optional[FlatTags]]]:
        return self.tags.all().order_by('slug')


@strawberry.type
class PostBlock:
    """
    PostPage block for StreamField
    """

    value: GenericScalar

    @strawberry.field
    def post(self) -> Optional[PostNode]:
        return PostPage.objects.get(id=self.value, live=True)


@strawberry_django.type(BlogIndexPage, pagination=True)
class BlogIndexNode(strawberry.relay.Node):
    """
    Relay: Blog index page node
    """

    id: strawberry.relay.NodeID[int]
    title: str
    slug: str
    numchild: int
    url_path: str
    seo_title: str
    search_description: str
    description: str
    image: ImageNode

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.live()


@strawberry.type
class BlogQuery:
    """
    Blog Query definition
    """

    blog_index: Optional[BlogIndexNode] = strawberry_django.field(extensions=[IsAuthenticated()])

    @strawberry_django.connection(Connection[BlogIndexNode], extensions=[IsAuthenticated()])
    def blog_indices(self) -> Iterable[BlogIndexNode]:
        return BlogIndexPage.objects.all()

    @strawberry.field(extensions=[IsAuthenticated()])
    def post(root, slug: str) -> Optional[PostNode]:
        post = None
        try:
            post = PostPage.objects.get(
                slug__iexact=slug,
                live=True)
        except PostPage.DoesNotExist:
            pass

        return post

    @strawberry_django.connection(Connection[PostNode], extensions=[IsAuthenticated()])
    def posts(
        self,
        order_by: Optional[List[Optional[str]]] = strawberry.UNSET,
        pagination: Optional[OffsetPaginationInput] = strawberry.UNSET
    ) -> Iterable[PostNode]:
        order = [] if order_by is strawberry.UNSET else order_by
        posts = PostPage.objects.all().order_by(*order)
        return strawberry_django.pagination.apply(pagination, posts)
