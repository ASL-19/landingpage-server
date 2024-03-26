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


import boto3
import json
import gzip
import io
from django.conf import settings


class S3Manager:
    def __init__(self):
        self.s3_client = boto3.client(
            's3', region_name=settings.S3_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=boto3.session.Config(signature_version='s3v4'))

    def write_content_to_s3(self, content, key):
        """
        Write the content to S3 key

        Args:
        config_data: A dictionary containing all the data to be written
        key: The target key on S3
        """
        self.s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Body=content)

    def read_content_from_s3(self, key):
        """
        read a content stored on s3 bucket related to the app

        Args:
        key the key pointing to the content it is like
        """
        result = self.s3_client.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key)

        return result['Body'].read(result['ContentLength'])

    def read_dict_from_s3(self, key):
        try:
            return json.loads(self.read_content_from_s3(key))

        except ValueError:
            return None

    def write_config_to_s3(self, config_data, key, gzipped=False):
        """
            Writes the JSON config file to S3

            Args:
            config_data: A dictionary containing all the data to be written
        """
        buffer = json.dumps(config_data)
        if gzipped:
            buffer = io.StringIO()
            writer = gzip.GzipFile(None, 'wb', 9, buffer)
            writer.write(json.dumps(config_data))
            writer.close()
            buffer.seek(0)
            key += '.gz'

        self.write_content_to_s3(buffer, key)

        if gzipped:
            buffer.close()

        def get_s3_temp_url(self, version):
            """
            Get s3 temp url using api credentials
            """
            if not version.s3_key:
                return ''
            expiry = 600
            key_id = settings.AWS_ACCESS_KEY_ID
            secret_key = settings.AWS_SECRET_ACCESS_KEY
            session = boto3.Session(
                aws_access_key_id=key_id,
                aws_secret_access_key=secret_key)
            s3_config = boto3.Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'})
            s3_client = session.client(
                's3',
                settings.S3_REGION,
                config=s3_config)
            try:
                link = s3_client.generate_presigned_url(
                    ExpiresIn=expiry,
                    ClientMethod='get_object',
                    Params={
                        'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                        'Key': version.s3_key.strip('/'),
                    })
            except boto3.ClientError as error:
                raise boto3.FieldError('Error generating s3 temp link for version: {}'.format(str(error)))
            return link
