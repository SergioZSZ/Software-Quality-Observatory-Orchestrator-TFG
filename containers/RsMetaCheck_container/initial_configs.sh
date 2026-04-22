#!/bin/sh

echo "configuring somef..."
printf "%s\n\n\n\n\n\n" "$GITHUB_TOKEN" | somef configure

exec "$@"
