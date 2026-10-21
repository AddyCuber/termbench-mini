#!/usr/bin/env bash
set -euo pipefail

grep -qx 'WORKERS=4' /etc/default/termbench-worker || { echo 'FAIL: worker count is not 4' >&2; exit 1; }
grep -qx 'MODE=production' /etc/default/termbench-worker || { echo 'FAIL: production mode changed' >&2; exit 1; }