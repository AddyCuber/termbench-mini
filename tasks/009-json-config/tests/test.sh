#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path('/etc/termbench/service.json').read_text())
assert data == {'service': 'catalog', 'port': 8080}
PY