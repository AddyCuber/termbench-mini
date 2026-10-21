#!/usr/bin/env bash
set -euo pipefail

[[ "$(readlink /opt/releases/current)" == "/opt/releases/release-2026-10" ]] || { echo 'FAIL: current release link is wrong' >&2; exit 1; }
[[ "$(cat /opt/releases/current)" == "release-2026-10" ]] || { echo 'FAIL: current release content is wrong' >&2; exit 1; }