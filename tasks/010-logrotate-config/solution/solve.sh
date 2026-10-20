#!/usr/bin/env bash
set -euo pipefail

sed -i 's|/var/log/syslog|/var/log/termbench/app.log|' /etc/logrotate.d/termbench