#!/usr/bin/env bash
set -euo pipefail

cd /work
make clean >/dev/null || { echo 'FAIL: make clean failed' >&2; exit 1; }
make >/dev/null || { echo 'FAIL: make failed' >&2; exit 1; }
[[ "$(./distance)" == "5.0" ]] || { echo 'FAIL: distance output was not 5.0' >&2; exit 1; }