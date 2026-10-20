#!/usr/bin/env bash
set -euo pipefail

sshd -t
grep -qx 'Port 2222' /etc/ssh/sshd_config.d/termbench.conf
grep -qx 'PasswordAuthentication no' /etc/ssh/sshd_config.d/termbench.conf