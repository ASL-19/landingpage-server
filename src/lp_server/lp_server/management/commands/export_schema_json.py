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

import json
import pathlib
import sys

from django.core.management.base import BaseCommand, CommandError
from strawberry import Schema
from strawberry.printer import print_schema
from strawberry.utils.importer import import_module_symbol

from lp_server.schema import schema


class Command(BaseCommand):
    help = "Export the graphql schema"  # noqa: A003

    def add_arguments(self, parser):
        parser.add_argument("schema", nargs=1, type=str, help="The schema location")
        parser.add_argument("--path", nargs="?", type=str, help="Optional path to export")

    def handle(self, *args, **options):
        try:
            schema_symbol = import_module_symbol(options["schema"][0], default_symbol_name="schema")
        except (ImportError, AttributeError) as e:
            raise CommandError(str(e)) from e

        if not isinstance(schema_symbol, Schema):
            raise CommandError("The `schema` must be an instance of strawberry.Schema")

        schema_output = print_schema(schema_symbol)
        path = options.get("path")
        if path:
            if path and path.endswith('.json'):
                schema_output = json.dumps(
                    {
                        "data": schema.introspect()
                    },
                    indent=4,
                    sort_keys=True
                )
            with pathlib.Path(path).open("w") as f:
                f.write(schema_output)
        else:
            sys.stdout.write(schema_output)
