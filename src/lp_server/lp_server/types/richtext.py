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

from wagtail.rich_text import expand_db_html
from lp_server.media_storage import get_s3_url

from typing import NewType


def serialize(value):
    """
    Serialises RichText content into fully baked HTML
    see https://github.com/wagtail/wagtail/issues/2695#issuecomment-373002412
    """
    s3_url = get_s3_url()
    html = expand_db_html(value)
    if s3_url is not None:
        html = html.replace(s3_url, '')

    return html


RichTextFieldType = strawberry.scalar(
    NewType("RichTextFieldType", object),
    description="Serialises RichText content into fully baked HTML",
    serialize=lambda v: serialize(v),
    parse_value=lambda v: v,
)
