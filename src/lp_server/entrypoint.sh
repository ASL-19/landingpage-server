#!/bin/bash

# Waiting for postgresql to start accepting connections
echo "Waiting for postgres..."
while !</dev/tcp/$DATABASE_HOST/$DATABASE_PORT; do
  sleep 0.1
done 2>/dev/null
sleep 2
echo "PostgreSQL started"

exec "$@"
