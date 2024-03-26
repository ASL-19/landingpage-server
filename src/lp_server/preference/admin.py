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

import pytz

from django.contrib import admin
from django import forms
from django.conf.locale import LANG_INFO

from preference.models import (
    Text,
    Location
)


class GeographyForm(forms.ModelForm):

    timezone = forms.ChoiceField(
        choices=[
            (timezone, timezone)
            for timezone in pytz.common_timezones
        ],
    )

    language = forms.ChoiceField(
        choices=[
            (LANG_INFO[lang]['name'], LANG_INFO[lang]['name'])
            for lang in LANG_INFO if len(lang) == 2
        ]
    )


class LocationAdmin(admin.ModelAdmin):
    fields = (
        'country',
        'city',
        'timezone',
        'language'
    )

    form = GeographyForm

    list_display = (
        'country',
        'city',
    )

    search_fields = (
        'country',
        'city'
    )


admin.site.register(Text)
admin.site.register(Location, LocationAdmin)
