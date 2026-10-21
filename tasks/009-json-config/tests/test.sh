#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path('/etc/termbench/service.json').read_text())
if data != {'service': 'catalog', 'port': 8080}:
	print('FAIL: service JSON has wrong values')
	raise SystemExit(1)
PY