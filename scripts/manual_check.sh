#!/usr/bin/env bash
# Prove a task is broken, then that solution/solve.sh makes tests pass.
# Build context is environment/ only; tests and solution are docker-cp'd in.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${1:?usage: $0 <task_id_prefix>}"

shopt -s nullglob
matches=("$ROOT/tasks/${PREFIX}"*)
shopt -u nullglob
if [[ ${#matches[@]} -ne 1 || ! -d "${matches[0]}" ]]; then
  echo "expected exactly one task directory for prefix '${PREFIX}'" >&2
  exit 1
fi

TASK_DIR="${matches[0]}"
TASK_ID="$(basename "$TASK_DIR")"
IMAGE="termbench-${TASK_ID}"
CID=""

cleanup() {
  if [[ -n "${CID}" ]]; then
    docker rm -f "${CID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "== build ${IMAGE} (context: ${TASK_DIR}/environment) =="
docker build -t "${IMAGE}" "${TASK_DIR}/environment"

echo "== start container (--network none, --memory 1g, --cpus 1) =="
CID="$(docker run -d \
  --network none \
  --memory 1g \
  --cpus 1 \
  "${IMAGE}" \
  sleep infinity)"

run_tests() {
  docker exec "${CID}" rm -rf /tmp/termbench-tests
  docker exec "${CID}" mkdir -p /tmp/termbench-tests
  docker cp "${TASK_DIR}/tests/." "${CID}:/tmp/termbench-tests"
  docker exec "${CID}" bash /tmp/termbench-tests/test.sh
}

echo "== tests BEFORE solution (must FAIL) =="
if run_tests; then
  echo "UNEXPECTED PASS: tests succeeded on the untouched machine"
  exit 1
fi
echo "FAIL (expected before solution)"

echo "== copy and run solution/solve.sh =="
docker exec "${CID}" rm -rf /tmp/termbench-solution
docker exec "${CID}" mkdir -p /tmp/termbench-solution
docker cp "${TASK_DIR}/solution/." "${CID}:/tmp/termbench-solution"
docker exec "${CID}" bash /tmp/termbench-solution/solve.sh

echo "== tests AFTER solution (must PASS) =="
if ! run_tests; then
  echo "UNEXPECTED FAIL: tests did not pass after solution"
  exit 1
fi
echo "PASS (expected after solution)"
