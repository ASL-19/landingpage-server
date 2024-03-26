# -*- coding: utf-8 -*-
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

import bs4
from django.db import models
from django.core.management import settings

from django.utils.html import (
    format_html, format_html_join
)
from django.forms.utils import flatatt

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail import blocks
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel
)
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailmedia.blocks import AbstractMediaChooserBlock
from wagtail.search import index

from lp_server.models import TranslatablePageMixin


class BlogIndexPage(Page, TranslatablePageMixin):
    """
    Blog index page
    """

    description = RichTextField()
    # We include related_name='+' to avoid name collisions on relationships.
    # e.g. there are two FooPage models in two different apps,
    # and they both have a FK to Image, they'll both try to create a
    # relationship called `foopage_objects` that will throw a valueError on
    # collision.
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.PROTECT,
        related_name='+')

    subpage_types = [
        'PostPage',
    ]

    # Only allowed to be created under root
    parent_page_types = [
        Page,
    ]

    search_fields = Page.search_fields + [
        index.SearchField('description'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('description', classname='full'),
        FieldPanel('image'),
        MultiFieldPanel(TranslatablePageMixin.panels, 'Language links'),
    ]

    max_count_per_parent = len(settings.LANGUAGES)


class PostTag(TaggedItemBase):
    """
    Tags for blog posts
    """

    content_object = ParentalKey(
        'PostPage',
        related_name='tagged_items',
        on_delete=models.CASCADE)


class MediaChooserBlock(AbstractMediaChooserBlock):
    """
    Media chooser block for streamfield
    """

    def render_basic(self, value, context=None):
        if not value:
            return ''

        if value.type == 'video':
            player_code = '''
            <div>
                <video width='320' height='240' controls>
                    {0}
                    Your browser does not support the video tag.
                </video>
            </div>
            '''
        else:
            player_code = '''
            <div>
                <audio controls>
                    {0}
                    Your browser does not support the audio element.
                </audio>
            </div>
            '''

        return format_html(player_code, format_html_join(
            '\n', '<source{0}>',
            [[flatatt(s)] for s in value.sources]
        ))


class PostPage(Page, TranslatablePageMixin):
    """
    A django model to define the blog post page
    """

    published = models.DateField(
        'Post date')
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.PROTECT,
        related_name='+')
    read_time = models.FloatField(
        null=True,
        blank=True)
    featured = models.BooleanField(
        default=False)
    synopsis = models.TextField(
        blank=True)
    summary = RichTextField(
        blank=True)
    body = StreamField(
        [
            ('heading', blocks.CharBlock(classname='full title')),
            ('paragraph', blocks.RichTextBlock()),
            ('image', ImageChooserBlock()),
            ('document', DocumentChooserBlock()),
            ('media', MediaChooserBlock(icon='media')),
            ('collapsible', blocks.RichTextBlock()),
            ('related_posts', blocks.ListBlock(
                blocks.PageChooserBlock(
                    target_model=('blog.PostPage', )))),
        ], use_json_field=True)
    tags = ClusterTaggableManager(
        through=PostTag,
        blank=True)

    def word_count(self, html):
        WORD_LENGTH = 5

        def extract_text(html):
            soup = bs4.BeautifulSoup(html, 'html.parser')
            texts = soup.findAll(text=True)
            return texts

        def is_visible(element):
            if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
                return False
            elif isinstance(element, bs4.element.Comment):
                return False
            elif element.string == '\n':
                return False
            return True

        def filter_visible_text(page_texts):
            return filter(is_visible, page_texts)

        def count_words_in_text(text_list, word_length):
            total_words = 0
            for current_text in text_list:
                total_words += len(current_text) / word_length
            return total_words

        texts = extract_text(html)
        filtered_text = filter_visible_text(texts)
        return count_words_in_text(filtered_text, WORD_LENGTH)

    def save(self, *args, **kwargs):
        """
        Calculate read_time if it's not provided
        from: https://github.com/assafelovic/reading_time_estimator
        """

        WPM = 200.0
        total_words = 0.0
        for block in self.body:
            if block.block.__class__.__name__ in ('CharBlock', 'RichTextBlock'):
                total_words += self.word_count(str(block.value))

        self.read_time = total_words / WPM

        super(PostPage, self).save(*args, **kwargs)

    # Only allowed to be created under root
    parent_page_types = [
        'BlogIndexPage',
    ]

    # Specifies what content types can exist as children of PostPage.
    # Empty list means that no child content types are allowed.
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('published'),
            FieldPanel('tags'),
            FieldPanel('featured'),
        ], heading='Post Information'),
        FieldPanel('featured_image'),
        # FieldPanel('read_time'),    # We can re-enable this once wagtail supports readonly panels
        FieldPanel('synopsis', classname='full'),
        FieldPanel('summary'),
        FieldPanel('body'),
    ]
