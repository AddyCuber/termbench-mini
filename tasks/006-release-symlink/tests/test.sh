#!/usr/bin/env bash
set -euo pipefail

[[ "$(readlink /opt/releases/current)" == "/opt/releases/release-2026-10" ]]
[[ "$(cat /opt/releases/current)" == "release-2026-10" ]]