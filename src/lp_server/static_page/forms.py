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

import magic
from wagtail.documents.forms import BaseDocumentForm
from wagtailmedia.forms import BaseMediaForm
from django import forms


class CustomDocumentForm(BaseDocumentForm):
    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        # Validate uploaded documents content-type based on accepted extensions
        allowable_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/rtf',
            'text/rtf',
            'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.oasis.opendocument.text',
            'application/vnd.oasis.opendocument.spreadsheet',
            'application/vnd.oasis.opendocument.presentation',
        ]
        try:
            filetype = magic.from_buffer(file.read(2048), mime=True)
            if filetype not in allowable_types:
                raise forms.ValidationError('The file was not uploaded. File type is not permitted.')
        except ValueError:
            raise forms.ValidationError('The file was not uploaded. File type is not permitted.')

        return file


class CustomMediaForm(BaseMediaForm):
    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        # Validate uploaded documents content-type based on accepted extensions
        allowable_types = [
            'audio/aac',
            'audio/mpeg',
            'audio/flac',
            'audio/mp3',
            'audio/mp4',
            'video/mp4',
            'audio/ogg',
            'video/ogg',
            'audio/wave',
            'audio/wav',
            'audio/x-wav',
            'audio/x-pn-wav',
            'audio/webm',
            'video/webm',
            'video/quicktime',
            'video/x-msvideo',
            'audio/aiff',
            'audio/x-aiff',
        ]
        try:
            filetype = magic.from_buffer(file.read(2048), mime=True)
            if filetype not in allowable_types:
                raise forms.ValidationError('The file was not uploaded. File type is not permitted.')
        except ValueError:
            raise forms.ValidationError('The file was not uploaded. File type is not permitted.')

        return file
