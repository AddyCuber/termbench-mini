#!/usr/bin/env bash
set -euo pipefail

sed -i 's|/tmp/wrong|/srv/restored|' /usr/local/bin/restore-app.sh