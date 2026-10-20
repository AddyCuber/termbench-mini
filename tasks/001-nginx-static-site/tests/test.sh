#!/usr/bin/env bash
# Outcome checks only. Expected hashes are of the original page files.
set -euo pipefail

INDEX_SHA="2348677033352bc879d9c4a21d1408d45e45424252380ae0698bfd6a4d3f3003"
ABOUT_SHA="6fbef4f637e0f2e021ee52a82d78b8a82078a22f45a8f8fa2664183fbc67ce6b"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

pgrep -x nginx >/dev/null 2>&1 || fail "nginx process is not running"

nginx -t >/dev/null 2>&1 || fail "nginx -t did not pass"

http_get() {
  local url="$1"
  local body="/tmp/termbench-body"
  local code
  code=$(curl -sS -o "$body" -w "%{http_code}" "$url") || fail "curl failed for $url"
  echo "$code"
}

code=$(http_get "http://localhost:8080/")
[[ "$code" == "200" ]] || fail "GET / expected 200, got $code"
grep -q "Welcome to Acme Widgets" /tmp/termbench-body || fail "GET / missing expected text"

code=$(http_get "http://localhost:8080/about.html")
[[ "$code" == "200" ]] || fail "GET /about.html expected 200, got $code"
grep -q "About Acme" /tmp/termbench-body || fail "GET /about.html missing expected text"

code=$(http_get "http://localhost:8080/does-not-exist")
[[ "$code" == "404" ]] || fail "GET /does-not-exist expected 404, got $code"

got=$(sha256sum /srv/site/index.html | awk '{print $1}')
[[ "$got" == "$INDEX_SHA" ]] || fail "index.html content was changed"

got=$(sha256sum /srv/site/about.html | awk '{print $1}')
[[ "$got" == "$ABOUT_SHA" ]] || fail "about.html content was changed"
