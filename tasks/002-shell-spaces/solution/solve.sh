#!/usr/bin/env bash
set -euo pipefail

sed -i 's/for path in \$@;/for path in "$@";/' /usr/local/bin/archive-list.sh