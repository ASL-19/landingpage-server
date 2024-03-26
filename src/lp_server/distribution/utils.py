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

import re
import logging
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


def str2bool(txt):
    if txt.lower() == 'true':
        return True
    else:
        return False


def get_key_dict(keys):
    """
    Populate Outline Key

    :param user: Vpnuser object to get their keys
    :return: List of user keys
    """
    keys_list = []
    if keys:
        for key in keys:
            keys_list.append({
                'id': key.id,
                'outline_key_id': key.outline_key_id,
                'server': key.server.id,
                'outline_key': key.outline_key
            })
    return keys_list


def base64_padding(txt):
    if len(txt) % 4:
        # not a multiple of 4, add padding:
        txt += '=' * (4 - len(txt) % 4)
    return txt


class OnlineConfigException(Exception):
    """ Base class for exceptions in OnlineConfigException """
    def __init__(self, value):
        """ Set value of error message """
        super(OnlineConfigException, self).__init__()
        self.value = value

    def __str__(self):
        """ Output representation of error """
        return repr(self.value)


class AWSError(OnlineConfigException):
    """ AWS API Error Wrapper """


class FeedbackError(OnlineConfigException):
    """ Feedback Error Wrapper """


class TelegramError(OnlineConfigException):
    """ Telegram Error Wrapper """


class ValidationError(OnlineConfigException):
    """ Validation Error Wrapper """


class HTTPError(OnlineConfigException):
    """ HTTP Error on Requests """


class DBError(OnlineConfigException):
    """ DB Errors """


def put_file_on_S3(bucket, key, content, content_type=None, cache_control=None):
    """
    Get a file from S3 using Specific Credentials

    Args:
        bucket: name of bucket
        key: key id in bucket
        content: file body content
        content_type (str): The content type of the file (e.g. "application/json").
        cache_control (str): The cache control header to set for the file (e.g. "max-age=3600").
    Raises:
        AWSError: couldn't fetch file contents from S3
    """
    if key is None or len(key) <= 0:
        raise ValidationError("Key name cannot be empty.")

    if bucket is None or len(bucket) <= 0:
        raise ValidationError("Bucket name cannot be empty.")

    s3_resource = boto3.resource("s3")

    # Create a dictionary of optional parameters
    optional_params = {}
    if content_type:
        optional_params["ContentType"] = content_type
    if cache_control:
        optional_params["CacheControl"] = cache_control

    try:
        s3_new_file = s3_resource.Object(bucket, key)
        s3_new_file.put(
            Body=content,
            **optional_params)

    except ClientError as error:
        raise AWSError("Problem putting {} from {} bucket ({})"
                       .format(key, bucket, str(error)))
    return


def delete_file_from_s3(bucket, key):
    """ Delete a file from S3 using Specific Credentials

    Args:
        bucket: name of bucket
        key: key id in bucket
    Returns:
        Stream object with contents
    Raises:
        AWSError: couldn't fetch file contents from S3
    """
    if key is None or len(key) <= 0:
        raise ValidationError("Key name cannot be empty.")

    if bucket is None or len(bucket) <= 0:
        raise ValidationError("Bucket name cannot be empty.")

    s3_resource = boto3.resource("s3")
    try:
        s3_file = s3_resource.Object(bucket, key)
        s3_file.delete()
    except ClientError as error:
        raise AWSError("Error deleting file from S3: {}".format(str(error)))
    return


def replace_ip(outline_key, host_name):
    pattern = r"\@(.*)\:"
    try:
        logger.debug(f'Replacing server IP with {host_name} in {outline_key}')
        return re.sub(pattern, f'@{host_name}:', outline_key, count=0, flags=0)
    except Exception as error:
        logger.error(f'Unable to replace Outline IP address with the new hostname {error}')
        return None


def replace_port(outline_key, new_port):
    pattern = r"\:(\d{2,})\/"
    gtf_pattern = r"\:(\d{2,})\?outline"

    try:
        logger.debug(f'Replacing the port with {new_port} in {outline_key}')
        if re.findall(gtf_pattern, outline_key):
            return re.sub(gtf_pattern, f':{new_port}?outline', outline_key, count=0, flags=0)
        return re.sub(pattern, f':{new_port}/', outline_key, count=0, flags=0)
    except Exception as error:
        logger.error(f'Unable to replace the port: {error}')
        return None
