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

from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.models import (
    Page, Orderable,
)
from wagtail.admin.panels import (
    FieldPanel, InlinePanel
)
from wagtail.fields import StreamField
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail import blocks

from blog.models import MediaChooserBlock
from preference.models import Faq


class StaticPage(Page):
    """
    Static Pages to be defined for the site
    """

    published = models.DateField(
        'Post Date')

    body = StreamField(
        [
            ('heading', blocks.CharBlock(classname='full title')),
            ('paragraph', blocks.RichTextBlock()),
            ('image', ImageChooserBlock()),
            ('document', DocumentChooserBlock()),
            ('media', MediaChooserBlock(icon='media')),
            ('link', blocks.URLBlock()),
            ('email', blocks.EmailBlock()),
        ], use_json_field=True)

    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+')

    parent_page_types = [Page, ]

    content_panels = Page.content_panels + [
        FieldPanel('published'),
        FieldPanel('body'),
        FieldPanel('image'),
        InlinePanel('faqs', label='FAQ(s)', panels=None),
    ]


class StaticPageFaqRelationship(Orderable):
    """
    This defines the relationship between the `Faq` and the StaticPage model.
    This allows Faqs to be added to a StaticPage.

    We have created a two way relationship between StaticPage and Faq using
    the ParentalKey and ForeignKey
    """

    page = ParentalKey(
        StaticPage,
        on_delete=models.CASCADE,
        related_name='faqs')

    faq = models.ForeignKey(
        Faq,
        on_delete=models.CASCADE,
        related_name='pages')

    panels = [
        FieldPanel('faq')
    ]
