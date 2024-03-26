#!/bin/sh
set -e -v

# Check linters
pip install -r test_requirements.txt
flake8 --config=linters.config

# Django test command
./manage.py test

# Generate GraphQL schema
# .GRAPHQL
./manage.py export_schema lp_server.schema --path schema.graphql

# .JSON
./manage.py export_schema_json lp_server.schema --path schema.json
