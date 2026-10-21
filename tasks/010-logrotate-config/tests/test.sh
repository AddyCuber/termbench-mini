#!/usr/bin/env bash
set -euo pipefail

grep -q '^/var/log/termbench/app.log {' /etc/logrotate.d/termbench || { echo 'FAIL: log path is wrong' >&2; exit 1; }
grep -q '^    rotate 7$' /etc/logrotate.d/termbench || { echo 'FAIL: retention is not 7' >&2; exit 1; }