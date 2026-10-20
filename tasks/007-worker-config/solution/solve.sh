#!/usr/bin/env bash
set -euo pipefail

sed -i 's/^WORKERS=.*/WORKERS=4/' /etc/default/termbench-worker