#!/usr/bin/env bash
set -euo pipefail

mkdir -p /srv/restored
tar -xf /opt/app-backup.tar -C /tmp/wrong