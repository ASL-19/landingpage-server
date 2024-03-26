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
from distribution.models import USER_CHANNEL_CHOICES
from server.models import OutlineServer
from preference.serializers import RegionField


class OutlineServerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=128,
        allow_blank=False)
    # ToDo: support ipv6
    ipv4 = serializers.IPAddressField(
        protocol="IPv4")
    provider = serializers.CharField(
        required=False)
    cost = serializers.FloatField(
        required=False)
    user_src = serializers.ChoiceField(
        choices=USER_CHANNEL_CHOICES,
        required=False)
    api_url = serializers.CharField()
    api_cert = serializers.CharField()
    prometheus_port = serializers.IntegerField(
        required=False)
    active = serializers.BooleanField(
        required=False)
    is_blocked = serializers.BooleanField(
        required=False)
    region = RegionField(
        required=False,
        many=True)
    level = serializers.IntegerField(
        required=False)
    dist_model = serializers.IntegerField()

    class Meta:
        model = OutlineServer
        fields = '__all__'
