# 03 — Validator

## What this is

The validator is a gate in front of any model run. It asks: is this task a trustworthy benchmark item? A task that already passes, flakes, leaks the answer, or can phone the internet is not a fair measurement. `termbench validate` must exit non-zero if any of seven checks fail.

## How data flows

1. Load `task.yaml`. Check 6 scans the **prompt** (not `notes`) for each string in `forbidden_in_prompt`.
2. `docker build` from `environment/` only (check 1). Build logs are captured so a failure has a reason, not a hang.
3. A fresh sandbox, **before** any `docker cp`: `find` for `*/tests/test.sh` and `*/solution/solve.sh` (check 5), then `curl -s --max-time 3 https://example.com` (check 7). Curl must fail.
4. Three **new** containers each: copy tests in, expect failure; copy `solve.sh` in, expect success. Check 2 is the first untouched failure, check 3 is the first post-solve success, check 4 requires the three `(before_exit, after_exit)` pairs to be identical.
5. Results print as `PASS`/`FAIL` with a reason, then a summary table `k/7`. The process exit code is 0 only if every check passed.

## Three questions you should be able to answer

1. Why does check 5 run before tests are copied in, and what path pattern does it look for?
2. How can check 4 pass while check 3 fails? What does that tell you about the task?
3. Why is a successful curl to example.com a failed check even if the hidden tests still pass?
