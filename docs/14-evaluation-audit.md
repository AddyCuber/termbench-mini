# Termbench-mini evaluation audit

This document follows the executable path, not just the prose documentation. Every factual statement below has a file-and-line citation. “Inference” marks a conclusion drawn from the code or from an absence of an enforcement mechanism, rather than a behavior directly asserted by a test.

## 1. Full pipeline and responsible files

1. **Task definition and resolution — `tasks/*/task.yaml`, `src/termbench/task.py`.** Each task declares an id, prompt, step and timeout budgets, prompt-leak strings, and notes; `load_task` parses those fields and exposes sibling `environment/`, `tests/`, and `solution/` directories through `Task` properties (`src/termbench/task.py:15-38`, `src/termbench/task.py:40-53`). A short id is resolved by exact match or by a unique prefix (`src/termbench/task.py:56-68`).

2. **Command dispatch — `src/termbench/cli.py`.** The CLI maps `validate` to `validator.validate`, `run` to `_run`, `batch` to `_batch`, and `report` to `write_report` (`src/termbench/cli.py:18-55`). `run` loads the task and builds its image before creating the run trace path (`src/termbench/cli.py:58-74`); `batch` delegates the repeated workflow to `runner.run_batch` (`src/termbench/cli.py:93-107`).

3. **Container build — `src/termbench/validator.py` plus each task’s `environment/Dockerfile`.** `build_image` calls `_build`, which runs `docker build -t termbench-{task.id}` with the task’s `environment` directory as the build context (`src/termbench/validator.py:25-33`, `src/termbench/validator.py:63-76`). The Dockerfiles install the task dependencies and copy only `environment/files` into the image; examples include nginx (`tasks/001-nginx-static-site/environment/Dockerfile:1-11`), OpenSSH (`tasks/004-sshd-config/environment/Dockerfile:1-9`), and Python for the JSON task (`tasks/009-json-config/environment/Dockerfile:1-7`).

4. **Task trust gate — `src/termbench/validator.py`.** Validation first checks that forbidden strings are absent from the prompt, builds the image, then checks image hygiene, fail/pass behavior, and network isolation (`src/termbench/validator.py:36-60`). The hygiene check searches for leaked test/solution paths and probes outbound network access (`src/termbench/validator.py:96-117`). Three fresh containers must show an untouched failure, a reference-solution success, and identical `(before, after)` exit-code pairs (`src/termbench/validator.py:120-159`).

5. **Agent loop — `src/termbench/agent.py` and `src/termbench/llm.py`.** `run_attempt` sends the system message and task prompt to `chat`, offers one bash function tool, executes each returned command through `Sandbox.exec`, and feeds stdout, stderr, and exit code back as tool output (`src/termbench/agent.py:12-31`, `src/termbench/agent.py:34-74`). The loop ends on a no-tool response, the task’s step limit, or the token limit (`src/termbench/agent.py:50-79`). `llm.chat` obtains `API_KEY`, `MODEL`, optional `BASE_URL`, temperature, and interval from the environment, then sends an OpenAI-format chat-completions request (`src/termbench/llm.py:39-67`).

6. **Sandbox execution — `src/termbench/sandbox.py`.** The sandbox starts a detached container with `--network none`, 1 GiB memory, 1 CPU, and `sleep infinity` (`src/termbench/sandbox.py:33-59`). Bash commands run with `docker exec ... bash -c` and a timeout (`src/termbench/sandbox.py:75-93`). The context manager force-removes the container on exit (`src/termbench/sandbox.py:21-31`, `src/termbench/sandbox.py:61-73`).

7. **Post-attempt grading — `src/termbench/runner.py`, `src/termbench/cli.py`, and `src/termbench/sandbox.py`.** After the model stops, the runner copies `tests/` into the existing container and runs `/tmp/termbench-tests/test.sh`; pass is exactly `verify.exit_code == 0` (`src/termbench/runner.py:83-93`). The single-run CLI uses the same rule (`src/termbench/cli.py:68-90`). `run_tests` performs the copy and executes the test script (`src/termbench/sandbox.py:121-123`).

8. **Aggregation and report — `src/termbench/runner.py` and `src/termbench/report.py`.** Batch builds each task once, runs each requested model/attempt, appends one result, and rewrites `results.json` after every attempt (`src/termbench/runner.py:16-62`). The report groups by `(task, model)`, counts pass/fail/budget/error outcomes, and reports median steps (`src/termbench/report.py:10-31`). It flags groups with at least two budget/error outcomes, zero passes, or at least five passes (`src/termbench/report.py:33-43`).

## 2. Exact pass/fail rule, inspected state, and check protection

### The rule

For a model attempt, the grader does not inspect the model’s final prose or compare it with `solution/solve.sh`. It copies the hidden test directory into the current container, runs `bash /tmp/termbench-tests/test.sh`, and sets `passed` to true only when that process exits zero (`src/termbench/sandbox.py:121-123`, `src/termbench/runner.py:91-93`). Therefore a non-zero test exit is `fail` unless the run itself raised an infrastructure/LLM error or hit the token cap; those are classified separately by `_outcome` (`src/termbench/runner.py:130-137`).

The inspected state is the **post-agent filesystem and process state in the same container**, plus whatever the test script explicitly checks. For example, task 001 checks nginx running, `nginx -t`, HTTP responses, and SHA-256 hashes of both page files (`tasks/001-nginx-static-site/tests/test.sh:13-40`); task 005 checks mode and exact content (`tasks/005-report-permissions/tests/test.sh:4-5`); task 009 parses JSON and requires exactly two key/value pairs (`tasks/009-json-config/tests/test.sh:4-12`).

### Why the agent normally cannot read or edit the check

- The image build is restricted to `environment/`; the validator’s build command does not include `tests/` or `solution/` (`src/termbench/validator.py:63-76`).
- The validator explicitly scans a fresh container before copying either directory (`src/termbench/validator.py:96-102`), and the agent run itself calls tests only after `run_attempt` returns (`src/termbench/runner.py:84-93`).
- The agent receives only one bash tool targeted at the container (`src/termbench/agent.py:20-31`, `src/termbench/sandbox.py:75-93`). The container has no network and no declared host mount or Docker socket (`src/termbench/sandbox.py:36-49`).

**Inference:** these measures prevent ordinary pre-attempt reads of the hidden files, but they do not prove resistance to a Docker escape or a vulnerable/host-integrated Docker daemon. The repository’s own design note calls Docker an imperfect security boundary and lists missing hardening such as rootless mode, dropped capabilities, syscall restrictions, and provenance controls (`docs/12-benchmark-design.md:7-9`, `docs/12-benchmark-design.md:45-56`).

### Ways to pass without the intended fix

**Inference:** because grading happens in the same mutable container after the agent stops, an agent can potentially arrange any state that satisfies the test, even if it does not implement the operational intent. The code does not snapshot or reset the container between the final agent state and verification (`src/termbench/runner.py:84-93`). Concrete examples are:

- A service task can be made to satisfy the tested process/HTTP state through a temporary or alternate configuration rather than the intended durable repair; task 001’s test checks the live nginx state and page hashes, not the precise repair path (`tasks/001-nginx-static-site/tests/test.sh:13-40`).
- A task can be solved by editing an unprotected equivalent or by creating the exact path/value the test reads when the prompt’s broader operational requirement is not tested. Task 008 checks only that the helper exits and that `/srv/restored/app.conf` contains one exact line (`tasks/008-backup-restore/tests/test.sh:4-5`).
- A verifier can reward a brittle textual state rather than semantic correctness: tasks 004, 007, and 010 use exact `grep` lines (`tasks/004-sshd-config/tests/test.sh:4-6`, `tasks/007-worker-config/tests/test.sh:4-5`, `tasks/010-logrotate-config/tests/test.sh:4-5`).

The hidden tests are unavailable during the loop, but the task prompt and the prebuilt filesystem reveal the general target. Prompt leak checks only reject explicitly listed strings in the prompt; they do not prove that the task is non-obvious or that all equivalent shortcuts are excluded (`src/termbench/validator.py:79-93`).

## 3. Task-design assumptions that can make a failure ambiguous

These are assumptions embedded in the fixtures, prompts, tests, or validator. A failed attempt can mean “the model was weak” only if the assumption holds.

### Global assumptions

- **The base image and package repositories are available and stable.** Most tasks depend on `debian:12-slim`; tasks 001, 003, 004, and 009 install nginx, compiler tools, OpenSSH, or Python during build (`tasks/001-nginx-static-site/environment/Dockerfile:1-6`, `tasks/003-make-math/environment/Dockerfile:1-5`, `tasks/004-sshd-config/environment/Dockerfile:1-7`, `tasks/009-json-config/environment/Dockerfile:1-5`). A registry, mirror, package, or architecture problem is not a model failure. **Inference:** the validator’s “builds cleanly” gate catches some of this before model runs, but it does not make every runtime dependency deterministic.
- **The Docker host behaves as expected.** The design admits host-runtime dependence (`docs/12-benchmark-design.md:35-43`), while the sandbox checks only network, memory, and CPU flags (`src/termbench/sandbox.py:36-49`). A daemon or kernel difference can therefore be confounded with model ability.
- **The step/token/time budgets are sufficient.** Budgets are task-specific (`tasks/*/task.yaml:5-7`) and the loop stops at either limit (`src/termbench/agent.py:50-79`). A budget failure may be search inefficiency, a slow service, or a hard task rather than inability to solve it.
- **The prompt names a sufficiently unique operational target.** Prompts often specify one exact path/value while tests encode a narrower or different notion of success (`tasks/005-report-permissions/task.yaml:3-9`, `tasks/005-report-permissions/tests/test.sh:4-5`). Ambiguity in wording is not separately measured.
- **The reference solution is a trustworthy solvability oracle.** Validation runs `solution/solve.sh`, requires it to succeed, and then requires tests to pass (`src/termbench/validator.py:162-174`). This proves one checked path works, not that the intended task has no simpler equivalent or that the hidden test is complete; the design explicitly notes incomplete verifiers can reward brittle workarounds (`docs/12-benchmark-design.md:35-43`).

### Per-task assumptions

- **001 nginx:** nginx must be the expected process, listen on 8080, serve exactly the two fixture pages, return 404 for one missing URL, and retain both page contents; these are encoded in the test (`tasks/001-nginx-static-site/tests/test.sh:13-40`). The fixture assumes the three noted defects are the causal defects: nginx is stopped, the root is wrong, and index permissions block `www-data` (`tasks/001-nginx-static-site/task.yaml:4-9`).
- **002 shell spaces:** correctness is defined by exactly two sample arguments and exactly two output lines; other shell inputs, globbing, empty arguments, newlines, and error handling are not tested (`tasks/002-shell-spaces/tests/test.sh:4-9`). The fixture assumes unquoted positional expansion is the only relevant defect (`tasks/002-shell-spaces/task.yaml:4-9`).
- **003 make math:** `make clean`, then `make`, must produce `./distance` whose output is exactly `5.0` (`tasks/003-make-math/tests/test.sh:4-7`). This assumes the compiler/linker/platform produce the same output and that “keep source unchanged” is adequately represented by the test; the test does not hash the source (`tasks/003-make-math/task.yaml:3-9`, `tasks/003-make-math/tests/test.sh:4-7`).
- **004 sshd:** `sshd -t` must pass, one drop-in must contain exact port and password-auth lines, and no other authentication behavior is checked (`tasks/004-sshd-config/tests/test.sh:4-6`). The task assumes the invalid boolean is the only blocker and that the image’s generated host keys and `/run/sshd` setup are sufficient (`tasks/004-sshd-config/task.yaml:4-9`, `tasks/004-sshd-config/environment/Dockerfile:3-7`).
- **005 permissions:** “readable by every local user” is reduced to mode `644`, and content preservation is reduced to one exact string (`tasks/005-report-permissions/tests/test.sh:4-5`). This assumes Unix mode bits, rather than ACLs, groups, or another valid permission representation, are the intended contract (`tasks/005-report-permissions/task.yaml:3-9`).
- **006 release link:** the required representation is one exact absolute symlink target and one exact target-file content (`tasks/006-release-symlink/tests/test.sh:4-5`). The test does not establish that a deployment command actually reads the link or that the link has the expected ownership/relative form (`tasks/006-release-symlink/task.yaml:3-9`, `tasks/006-release-symlink/tests/test.sh:4-5`).
- **007 worker config:** correctness is exactly two lines, `WORKERS=4` and `MODE=production` (`tasks/007-worker-config/tests/test.sh:4-5`). Other syntax, duplicate keys, comments, consumers, and whether a worker process uses the value are not tested (`tasks/007-worker-config/task.yaml:3-9`, `tasks/007-worker-config/tests/test.sh:4-5`).
- **008 backup restore:** the helper must exit zero and leave one path containing one exact setting (`tasks/008-backup-restore/tests/test.sh:4-5`). The test does not check that the archive was used, that the helper remains correct for other archives, or that unrelated files were not changed (`tasks/008-backup-restore/task.yaml:3-9`, `tasks/008-backup-restore/tests/test.sh:4-5`).
- **009 JSON:** the file must parse and equal exactly `{'service': 'catalog', 'port': 8080}` (`tasks/009-json-config/tests/test.sh:4-12`). This assumes key order/whitespace do not matter—which is appropriate for JSON—but also assumes no additional valid configuration keys are allowed (`tasks/009-json-config/task.yaml:3-9`, `tasks/009-json-config/tests/test.sh:4-12`).
- **010 logrotate:** correctness is two matching lines in a file; the test does not run logrotate or validate the rule’s syntax/side effects (`tasks/010-logrotate-config/tests/test.sh:4-5`). It assumes the path and retention count are the complete intended contract (`tasks/010-logrotate-config/task.yaml:3-9`).

## 4. Sandbox boundary and cheat surface

### What the agent can reach

The agent is told it is root in a Linux container and can use bash (`src/termbench/agent.py:12-18`, `src/termbench/agent.py:20-31`). In practice it can execute arbitrary shell commands as the container’s default user through `docker exec`, and commands share the same container state across steps (`src/termbench/sandbox.py:75-93`, `src/termbench/agent.py:61-74`). The image contains the files copied by that task’s Dockerfile and any installed packages (`tasks/001-nginx-static-site/environment/Dockerfile:3-8`, `tasks/004-sshd-config/environment/Dockerfile:3-9`).

It cannot use the configured network, and the implementation declares no host volume or Docker socket (`src/termbench/sandbox.py:36-49`). Tests and the reference solution are outside the image until after the loop (`src/termbench/validator.py:63-76`, `src/termbench/runner.py:84-93`).

### What remains possible

**Inference:** the boundary limits ordinary access, not all cheating. The agent is root, the container is not read-only, capabilities are not dropped, and no seccomp/PID/read-only policy is set in `docker run` (`src/termbench/agent.py:12-18`, `src/termbench/sandbox.py:36-49`). A container escape or daemon vulnerability is outside the model’s intended task but is not formally ruled out; the repository itself says stronger hardening is needed (`docs/12-benchmark-design.md:7-9`, `docs/12-benchmark-design.md:45-56`).

Within the intended boundary, the most realistic shortcut is to make the post-attempt state satisfy the hidden assertions without implementing the prompt’s durable operational fix. This is possible because tests are copied after the loop but run in the already-modified container, with no fresh-container reset (`src/termbench/runner.py:84-93`). The verifier’s outcome-only nature is deliberate, but it means coverage and mutation resistance of each test determine whether “pass” means the intended solution or merely a tested state (`docs/12-benchmark-design.md:11-13`, `docs/12-benchmark-design.md:35-43`).

## 5. Recorded results and missing evaluator data

### Recorded per attempt

`runner._run_one` records task, model, attempt number, boolean `passed`, stop reason, derived outcome, step count, wall-clock seconds, input/output token counts, trace path, error text, and the last 1,000 characters of verifier output (`src/termbench/runner.py:103-118`). The trace records each bash command, stdout, stderr, exit code, cumulative tokens, and UTC timestamp (`src/termbench/agent.py:90-107`). Batch writes the JSON after every completed attempt (`src/termbench/runner.py:46-48`, `src/termbench/runner.py:121-123`).

### Missing or insufficient data for a strong evaluator

- No task version, git commit, image digest, Docker/runtime version, host architecture, or full task configuration is stored in the result object (`src/termbench/runner.py:103-118`). The design explicitly recommends recording image digest, commit, provider, temperature, and full configuration (`docs/12-benchmark-design.md:45-50`).
- No provider/base URL, sampling seed, or effective temperature is recorded, although the adapter uses `BASE_URL`, `MODEL`, and `TEMPERATURE` (`src/termbench/llm.py:39-51`).
- No verifier version, individual assertion result, complete stdout/stderr, final filesystem diff, process list, or final assistant message is recorded; only truncated verifier output and the bash trace are persisted (`src/termbench/runner.py:103-118`, `src/termbench/agent.py:50-59`, `src/termbench/agent.py:90-107`).
- Infrastructure failures are collapsed into a string error and `stop_reason: error`; the code does not distinguish API failure, Docker failure, test timeout, or container startup failure in the schema (`src/termbench/runner.py:94-118`). The design lists separating infrastructure errors from model failures as an improvement (`docs/12-benchmark-design.md:45-51`).
- The aggregate report stores counts and median steps only; it discards per-group token, wall-time, and error-rate summaries (`src/termbench/report.py:17-31`).

## 6. Three most fragile code areas

1. **Same-container post-hoc grading (`src/termbench/runner.py:84-93`).** It is essential to hide tests during the loop, but it also means the final verifier observes mutable state selected by the agent. There is no clean-room verification or before/after filesystem capture. This is the largest validity risk because a passing assertion can be detached from the intended repair (**Inference**, based on the cited control flow and test narrowness).

2. **The sandbox’s incomplete hardening (`src/termbench/sandbox.py:36-49`).** The code sets network, memory, and CPU limits but does not set rootless execution, dropped capabilities, read-only filesystem, PID limit, seccomp profile, or a user. The design acknowledges those omissions (`docs/12-benchmark-design.md:45-56`). A host/container-runtime issue can therefore become either a security problem or a non-model failure (**Inference**).

3. **Outcome/error accounting and budget boundaries (`src/termbench/agent.py:50-79`, `src/termbench/runner.py:94-137`).** A loop can stop on `max_steps` or token cap, while an API/Docker/runtime exception becomes a generic `error`; the final result retains only aggregate counts and truncated verifier output. Also, multiple tool calls in one model response increment `steps` inside the response loop, so the stop condition is checked only before requesting the next response (`src/termbench/agent.py:50-64`). This can make the effective step budget exceed the nominal value by the remainder of one response (**Inference**).

