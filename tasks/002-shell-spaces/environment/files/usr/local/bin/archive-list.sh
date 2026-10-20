#!/usr/bin/env bash
set -euo pipefail

for path in $@; do
    printf '%s\n' "$path"
done