#!/usr/bin/env bash
set -euo pipefail

sed -i 's/GSSAPIAuthentication maybe/GSSAPIAuthentication no/' /etc/ssh/sshd_config.d/termbench.conf