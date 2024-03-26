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

from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from taggit.models import Tag


class TagAdmin(ModelAdmin):
    """
    Model Admin for Tag
    """

    model = Tag
    menu_label = 'Tags'
    menu_icon = 'tag'
    menu_order = 101
    add_to_settings_menu = True
    exclude_from_explorer = False
    list_display = ('name', 'slug', )
    form_fields_exclude = ['slug', ]
    search_fields = ('name', )


modeladmin_register(TagAdmin)
