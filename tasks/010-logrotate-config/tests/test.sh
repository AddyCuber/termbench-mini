#!/usr/bin/env bash
set -euo pipefail

grep -q '^/var/log/termbench/app.log {' /etc/logrotate.d/termbench
grep -q '^    rotate 7$' /etc/logrotate.d/termbench