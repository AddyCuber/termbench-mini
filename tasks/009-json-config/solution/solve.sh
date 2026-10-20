#!/usr/bin/env bash
set -euo pipefail

sed -i 's/"port": 9090/"port": 8080/' /etc/termbench/service.json