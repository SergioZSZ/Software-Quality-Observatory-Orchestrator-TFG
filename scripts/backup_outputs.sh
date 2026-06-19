#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$REPO_ROOT/backups"
DATE="$(date +"%Y_%m_%d")"
BACKUP_NAME="outputs_${DATE}.tar.gz"

if [ "$#" -lt 1 ]; then
echo "Usage:"
echo "  bash backup_outputs.sh DIRECTORY [DIRECTORY2 ...]"
exit 1
fi

for DIR in "$@"; do
    if [ ! -d "$REPO_ROOT/$DIR" ]; then
        echo "Error: the directory does not exist:"
        echo "  $REPO_ROOT/$DIR"
        exit 1
fi
done

mkdir -p "$BACKUP_DIR"

echo "Creating backup:"
printf '  - %s\n' "$@"

(
cd "$REPO_ROOT"
tar -czf "backups/$BACKUP_NAME" -- "$@"
)

echo
echo "Backup created correctly:"
echo "  $BACKUP_DIR/$BACKUP_NAME"

echo
echo "Size:"
du -h "$BACKUP_DIR/$BACKUP_NAME"
