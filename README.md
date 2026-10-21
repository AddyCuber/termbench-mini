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

## Results and limitations

Task validation is complete. A real Mistral Ministral 14B attempt solved task 001 on attempt 6 after the agent prompt was tightened; weaker models can miss the final service-start step. The first five-attempt calibration batch scored 3/5. The one-attempt model comparisons archived under `results/` are pre-truncation pilot data and should not be mixed with later runs. Calibration is not yet complete across all ten tasks: the result files under `runs/` are exploratory and should not be treated as a statistically stable benchmark. Use the batch command to collect repeated attempts before comparing models.

## Task revisions

Tasks 001, 002, and 008 were revised after the first calibration. Task 001 now allows 25 steps because its 15-step cap was binding while agents were still verifying nginx. Tasks 002 and 008 now name their helper paths and make the helper scripts executable, removing an environment-discovery confound while preserving the original bugs. All task verifiers now print an explicit `FAIL:` reason before exiting nonzero. Because prompt wording, executable bits, and step caps changed together, any score movement is an aggregate revision effect, not evidence for one specific cause. Results from before these revisions remain in `results/` and are labeled pre-revision data; they must not be mixed with post-revision measurements.

See [docs/](docs/) for plain-language component notes and milestone questions.
