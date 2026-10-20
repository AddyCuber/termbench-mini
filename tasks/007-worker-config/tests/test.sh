#!/usr/bin/env bash
set -euo pipefail

grep -qx 'WORKERS=4' /etc/default/termbench-worker
grep -qx 'MODE=production' /etc/default/termbench-worker