#!/usr/bin/env bash
set -euo pipefail

cd /work
make clean >/dev/null
make >/dev/null
[[ "$(./distance)" == "5.0" ]] || exit 1