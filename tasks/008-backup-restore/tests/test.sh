#!/usr/bin/env bash
set -euo pipefail

bash /usr/local/bin/restore-app.sh
[[ "$(cat /srv/restored/app.conf)" == "mode=production" ]]