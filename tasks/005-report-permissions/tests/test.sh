#!/usr/bin/env bash
set -euo pipefail

[[ "$(stat -c '%a' /opt/daily-report.txt)" == 644 ]] || { echo 'FAIL: report mode is not 644' >&2; exit 1; }
[[ "$(cat /opt/daily-report.txt)" == "Daily report: all systems nominal." ]] || { echo 'FAIL: report content changed' >&2; exit 1; }