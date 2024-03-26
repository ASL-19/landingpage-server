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

from wagtail.documents import get_document_model

from lp_server.types.tag import FlatTags
from lp_server.types.generic import GenericScalar
from lp_server.media_storage import get_s3_url


Document = get_document_model()


@strawberry_django.type(Document, pagination=True)
class DocumentNode(strawberry.relay.Node):
    """
    Document Node
    """

    id: strawberry.relay.NodeID[int]
    file_size: Optional[int]
    url: Optional[str]
    file_type: Optional[str]
    content_type: Optional[str]
    file_hash: str
    title: str
    file: str
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
class DocumentBlock:
    """
    Document block for StreamField
    """

    id: uuid.UUID
    value: Optional[GenericScalar]

    @strawberry.field
    def document(self) -> Optional[DocumentNode]:
        return Document.objects.get(id=self.value)


@strawberry.type
class DocumentsQuery:
    """
    Document Query definition
    """

    @strawberry.field
    def document(self, pk: int) -> Optional[DocumentNode]:
        return Document.objects.get(pk=pk)

    documents: strawberry.relay.ListConnection[DocumentNode] = strawberry_django.connection()
