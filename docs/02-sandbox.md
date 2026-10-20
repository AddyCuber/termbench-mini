# 02 — Sandbox and basic validate

## What this is

`Sandbox` is a thin wrapper around one Docker container that stands in for a broken machine. The agent (later) never talks to Docker; it only runs shell commands inside this box. `termbench validate` uses the same box to prove a task is well-formed: hidden tests fail on the untouched image, then pass after the reference `solve.sh`.

## How data flows

1. `cli.py` parses `validate <task_id>` and calls `validator.validate`.
2. `task.py` resolves `001` (or a full id) to `tasks/<id>/task.yaml` and the sibling `environment/`, `tests/`, and `solution/` folders.
3. `validator` builds the image from `environment/` only (`docker build`, no Docker SDK).
4. It starts a `Sandbox`: `docker run -d --network none --memory 1g --cpus 1 IMAGE sleep infinity`.
5. `copy_in` uses `docker cp` to drop `tests/` at `/tmp/termbench-tests`. `run_tests` executes `test.sh` via `docker exec`. Output is truncated to 10k characters.
6. The first run must fail. Then `solution/` is copied in, `solve.sh` runs, and tests must pass.
7. Leaving the `with Sandbox(...)` block always `docker rm -f`s the container, including on exceptions.

## Three questions you should be able to answer

1. Why does `Sandbox` start `sleep infinity` instead of nginx (or the task's service)?
2. What is truncated, to what size, and why does `exec` return an exit code instead of raising on a failing command?
3. How does the context manager guarantee the container is removed if `solve.sh` throws or tests hang until timeout?
