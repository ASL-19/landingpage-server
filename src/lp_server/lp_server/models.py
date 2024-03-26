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

from wagtail.models import Page
from wagtail.admin.panels import PageChooserPanel


class DatedMixin(models.Model):
    class Meta:
        ordering = ['-id']
        abstract = True

    created_date = models.DateTimeField(
        auto_now_add=True)
    updated_date = models.DateTimeField(
        auto_now=True)


class TranslatablePageMixin(models.Model):
    """
    Provide link for english language
    """

    english_link = models.ForeignKey(
        Page,
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        related_name='+')

    panels = [
        PageChooserPanel('english_link'),
    ]

    def get_language(self):
        """
        This returns the language code for this page.
        """

        language_homepage = self.get_ancestors(inclusive=True).get(depth=3)

        return language_homepage.slug

    def persian_page(self):
        """
        This finds the persian version of this page
        """

        language = self.get_language()

        if language == 'fa':
            return self
        elif language == 'en':
            return type(self).objects.filter(english_link=self).first().specific

    def english_page(self):
        """
        This finds the english version of this page
        """

        persian_page = self.persian_page()

        if persian_page and persian_page.english_link:
            return persian_page.english_link.specific

    class Meta:
        abstract = True


class CloudFrontState(models.Model):
    """
    A model defining CF invalidation requests
    """

    should_invalidate_during_next_cron_tick = models.BooleanField(
        default=False)
