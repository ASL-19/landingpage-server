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

from functools import wraps

from accounts.models import Role
from lp_server.constants import Messages


def login_required(fn):
    @wraps(fn)
    def wrapper(cls, info, input_, **kwargs):
        user = info.context.request.user
        if not user.is_authenticated or user.is_anonymous:
            return cls(success=False, errors=Messages.UNAUTHENTICATED)
        elif user.organization is None:
            return cls(success=False, errors=Messages.NO_ORGANIZATION)
        return fn(cls, info, input_, **kwargs)

    return wrapper


def verification_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(cls, info, input_, **kwargs):
        user = info.context.request.user
        if not user.status.verified:
            return cls(success=False, errors=Messages.NOT_VERIFIED)
        return fn(cls, info, input_, **kwargs)

    return wrapper


def supervisor_role_required(fn):
    @wraps(fn)
    @verification_required
    def wrapper(cls, info, input_, **kwargs):
        user = info.context.request.user
        if user.role != Role.SUPERVISOR:
            return cls(success=False, errors=Messages.NOT_SUPERVISOR)
        return fn(cls, info, input_, **kwargs)

    return wrapper
