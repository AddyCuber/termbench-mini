#!/usr/bin/env bash
set -euo pipefail

sshd -t || { echo 'FAIL: sshd configuration is invalid' >&2; exit 1; }
grep -qx 'Port 2222' /etc/ssh/sshd_config.d/termbench.conf || { echo 'FAIL: port is not 2222' >&2; exit 1; }
grep -qx 'PasswordAuthentication no' /etc/ssh/sshd_config.d/termbench.conf || { echo 'FAIL: password authentication is not disabled' >&2; exit 1; }