# termbench-mini

Termbench-mini is a small benchmark of broken Linux machines. Each task builds a Docker image containing a controlled failure. A terminal-using model receives only the task prompt and a bash tool; hidden tests are copied in after the attempt and verify the outcome.

## Setup

Use Python 3.12, Docker, and `uv`. Create `.env` from `.env.example` and set an API key for an OpenAI-compatible endpoint:

```dotenv
BASE_URL=https://api.mistral.ai/v1
API_KEY=replace-with-a-key
MODEL=ministral-14b-2512
TEMPERATURE=0.7
LLM_MIN_INTERVAL_S=1.1
```

Load it before model commands:

```sh
set -a
source .env
set +a
```

## Commands

```sh
uv run termbench validate 001
uv run termbench run 001 --model "$MODEL" --attempt 1
uv run termbench batch --tasks all --models "$MODEL" --attempts 5
uv run termbench report runs/<run-id>/results.json
```

`validate` must pass before running a model on a task. Containers have no network, resource limits, host mounts, or Docker socket. Tests and reference solutions are never included in image build contexts.

## Task pack

The repository currently contains ten validated tasks covering nginx, shell quoting, Make linking, SSH configuration, permissions, release pointers, worker settings, backup restore, JSON configuration, and log rotation. Every task passes the seven validator checks for clean build, deterministic fail/pass behavior, image hygiene, prompt leak checks, and network isolation.

## Results

4 models x 10 tasks x 5 attempts, default sampling temperature (0.7), 30k token cap (40k and 25 steps for tasks 001, 002 and 008).

| Model | Passed (of 50) |
|---|---:|
| Ministral 3B | 17 |
| Ministral 8B | 28 |
| Ministral 14B | 37 |
| Codestral | 25 |

| Task | 3B | 8B | 14B | Codestral |
|---|---:|---:|---:|---:|
| 001 nginx static site | 2/5 | 0/5 | 3/5 | 0/5 |
| 002 shell spaces | 0/5 | 4/5 | 3/5 | 0/5 |
| 003 make math | 0/5 | 0/5 | 2/5 | 0/5 |
| 004 sshd config | 0/5 | 0/5 | 3/5 | 5/5 |
| 005 report permissions | 5/5 | 5/5 | 4/5 | 5/5 |
| 006 release symlink | 3/5 | 5/5 | 5/5 | 5/5 |
| 007 worker config | 0/5 | 1/5 | 3/5 | 5/5 |
| 008 backup restore | 3/5 | 4/5 | 5/5 | 1/5 |
| 009 JSON config | 3/5 | 5/5 | 5/5 | 4/5 |
| 010 logrotate | 1/5 | 4/5 | 4/5 | 0/5 |

Outcomes: `pass` = hidden tests passed, however the loop ended. `fail` = loop ended normally or at `max_steps` and tests failed. `budget` = token cap ended the loop and tests failed. `error` = API failure, timeout or crash.

Excluded: 10 error outcomes from `mistral-large-2512` (not available on the account).

## Findings

- Same-family models scored 17, 28 and 37 of 50 at 3B, 8B and 14B. Individual cells are noisy at n=5.
- Codestral has a different profile: 5/5 on 004 and 007, 0/5 on 001, 002 and 010. Its 001 failures all ended with nginx not running.
- Agents often fix the symptom by hand and leave the real fix undone (003, and 008 before revision).
- The validator caught three task bugs before any model ran: a compiler optimised away the intended linker error (003), sshd needed an unrelated missing directory (004), and a missing python3 in the image (009).
- Tasks 002 and 008 were partly testing whether the agent could find an unnamed, non-executable helper. The path was named, the helper was made executable and the step cap was raised. Old results are kept as pre-revision.

## Limits

- n=5 per cell, 4 models from one provider, hand-written tasks.
- Difficulty is measured on small open models, not frontier models.
- Tasks 001, 002 and 008 were revised after seeing low scores, so some rebound is expected. The prompt, executable bit and step cap changed together, so no single cause can be named.
- 4 of the 60 post-revision attempts (all 3B) ended on the token cap, so its post-revision numbers are slightly depressed.
- Built with Cursor.

See [docs/](docs/) for plain-language component notes and milestone questions.
