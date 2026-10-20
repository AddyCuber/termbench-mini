#!/usr/bin/env bash
# Confirm the local machine can run termbench (Docker + Python 3.12).
# Never print secret values.
set -euo pipefail

echo "docker: $(docker --version)"
echo "python: $(python3 --version)"

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ANTHROPIC_API_KEY: set"
else
  echo "ANTHROPIC_API_KEY: not set"
fi
