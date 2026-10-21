#!/usr/bin/env bash
set -euo pipefail

expected=$'/tmp/alpha report.txt\n/tmp/beta report.txt'
actual=$(bash /usr/local/bin/archive-list.sh "/tmp/alpha report.txt" "/tmp/beta report.txt")
[[ "$actual" == "$expected" ]] || {
    printf 'FAIL: output did not preserve paths\nexpected:\n%s\nactual:\n%s\n' "$expected" "$actual" >&2
    exit 1
}