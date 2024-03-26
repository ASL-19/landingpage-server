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

from rest_framework import serializers
from preference.models import Region


class RegionField(serializers.RelatedField):
    queryset = Region.objects.all()

    def to_representation(self, value):
        return {
            'id': value.id,
            'name': value.name
        }

    def to_internal_value(self, data):
        return data


class RegionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(
        required=False)
