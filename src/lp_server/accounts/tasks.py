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

from gqlauth.models import RefreshToken
from lp_server.celery import app


@app.task()
def revoke_refresh_token_delayed(user_id, token_id):
    """
    Keep rotated refresh token valid for a short period before revoking

    Args:
        user_id: The id of the user that should have all refresh tokens revoked
        token_id: The id of the newly created refresh token that should stay valid
    """
    # Revoke all old refresh tokens (older than current refresh token)
    # Don't revoke newer refresh tokens
    refresh_tokens = RefreshToken.objects.filter(
        user_id=user_id,
        revoked=None
    ).exclude(id__gte=token_id)
    for token in refresh_tokens:
        token.revoke()
