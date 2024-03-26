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
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry.extensions import AddValidationRules
from graphql.validation import NoSchemaIntrospectionCustomRule

from django.conf import settings

from accounts.schema import UserQuery, UserMutation
from lp_server.types.image import ImageQuery
from lp_server.types.media import MediaQuery
from publisher.schema import PublisherQuery, PublisherMutation
from blog.schema import BlogQuery
from preference.schema import PreferenceQuery
from static_page.schema import StaticPageQuery


@strawberry.type
class Query(
        UserQuery, PublisherQuery, BlogQuery, ImageQuery,
        MediaQuery, PreferenceQuery, StaticPageQuery):
    pass


@strawberry.type
class Mutation(UserMutation, PublisherMutation):
    pass


extensions = [
    DjangoOptimizerExtension,
]

# Disable Introspection in production
if settings.BUILD_ENV == 'production':
    extensions.append(AddValidationRules([NoSchemaIntrospectionCustomRule]))

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=extensions)
