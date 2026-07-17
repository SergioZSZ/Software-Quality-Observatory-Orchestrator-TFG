#!/bin/sh

echo "configuring somef..."
printf "%s\n\n\n\n\n\n\n\n\n\n2000\n" "$GITHUB_TOKEN" | somef configure

echo "configuring soca..."
printf "\n\n\n%s\n\n" "mytoken" | soca configure

exec "$@"
