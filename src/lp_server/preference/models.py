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


from django.db import models
from django.db.utils import ProgrammingError
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from ckeditor_uploader.fields import RichTextUploadingField
from django_countries.fields import CountryField
from wagtail.admin.panels import FieldPanel

from wagtail.snippets.models import register_snippet
from modelcluster.models import ClusterableModel


class PreferenceModel(models.Model):

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(PreferenceModel, self).save(*args, **kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        if cache.get(cls.__class__.__name__) is None:
            try:
                obj, created = cls.objects.get_or_create(pk=1)
            except ProgrammingError:
                return None

            if created:
                obj.set_cache()
        return cache.get(cls.__class__.__name__)

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    class Meta:
        abstract = True


class Text(PreferenceModel):
    """
        This class defines an API model to provide texts such as privacy policy,
        About, Contact information, etc.

        The class has provision for 3 languages for each text.
    """

    language = models.CharField(
        max_length=2,
        default='fa',
        verbose_name=_('Language'))
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Modified Time'))
    about = RichTextUploadingField(
        null=True,
        blank=True,
        verbose_name=_('About Paskoocheh'))
    contact_email = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_('Contact Email'))
    privacy_policy = RichTextUploadingField(
        null=True,
        blank=True,
        verbose_name=_('Privacy Policy'))
    terms_of_service = RichTextUploadingField(
        null=True,
        blank=True,
        verbose_name=_('Terms of Service'))

    def __str__(self):
        return self.language

    class Meta:
        verbose_name_plural = _('Web Texts')


class Region(models.Model):
    """
    Class to store different Regions for
    landing page
    """

    name = models.CharField(
        max_length=128)

    def __str__(self):
        return self.name


@register_snippet
class Faq(ClusterableModel):
    """
    A Django model that is displayed as a snippet within the admin due
    to the `@register_snippet` decorator.
    """

    question = models.TextField()
    answer = models.TextField()

    panels = [
        FieldPanel('question'),
        FieldPanel('answer'),
    ]

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'


class Location(models.Model):
    """
    Countries/Cities that our servers are located
    """

    country = CountryField(
        max_length=256
    )

    city = models.CharField(
        max_length=256,
        null=True,
        blank=True
    )

    timezone = models.CharField(
        max_length=64
    )

    language = models.CharField(
        max_length=64
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f'{self.country}:{self.city}'

    class Meta:
        verbose_name_plural = 'Countries'
        unique_together = (
            'country',
            'city'
        )
