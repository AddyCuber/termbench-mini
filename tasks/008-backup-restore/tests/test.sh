#!/usr/bin/env bash
set -euo pipefail

bash /usr/local/bin/restore-app.sh || { echo 'FAIL: restore helper failed' >&2; exit 1; }
[[ "$(cat /srv/restored/app.conf)" == "mode=production" ]] || { echo 'FAIL: restored configuration is wrong' >&2; exit 1; }