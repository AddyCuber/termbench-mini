#!/usr/bin/env bash
set -euo pipefail

[[ "$(stat -c '%a' /opt/daily-report.txt)" == 644 ]]
[[ "$(cat /opt/daily-report.txt)" == "Daily report: all systems nominal." ]]