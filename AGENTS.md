# Agent guidance

## Project shape

- `src/termbench/cli.py` owns the argparse entrypoint and command dispatch.
- `src/termbench/task.py` parses task metadata and resolves task directories.
- `src/termbench/sandbox.py` is the only container execution boundary.
- `src/termbench/validator.py` builds images and checks task trustworthiness.
- `src/termbench/agent.py` runs the model bash-tool loop; `llm.py` is the Anthropic adapter.
- Task Docker build contexts are under `tasks/*/environment/`; tests and reference solutions stay outside the image.

## Commands

```sh
bash scripts/check_env.sh
uv run termbench validate 001
uv run termbench run 001 --model "$MODEL" --attempt 1
uv run termbench batch --tasks all --models "$MODEL" --attempts 5
uv run termbench report runs/<run-id>/results.json
```

Set `ANTHROPIC_API_KEY` for Anthropic or `GEMINI_API_KEY` for Gemini. Set `MODEL` or pass `--model`, and use `--provider gemini` or `LLM_PROVIDER=gemini` for Gemini; do not hardcode model names or secrets.
For Gemini 3.x, set `GEMINI_THINKING_BUDGET=0` for fast benchmark tool calls; increase it only when reasoning latency is acceptable.

## Invariants

- Use Python 3.12, the standard library, `pyyaml`, and `anthropic`; do not add frameworks or Docker SDK usage.
- Keep containers on `--network none`, with resource limits and no host mounts or Docker socket.
- Hidden tests and `solution/solve.sh` must be copied into a running container only after the image is built; never include them in an image build context.
- Verifiers must check outcomes and preserve task file content where the task requires it.
- Always clean up containers through `Sandbox`'s context manager.
- Add a focused study note under `docs/` for each completed milestone; link to existing notes instead of duplicating them.

## Validation

Run the narrowest relevant command after edits. For task or sandbox changes, finish with `uv run termbench validate <task_id>`. Do not run a model against a new task until validation passes.

See [README.md](README.md) and [docs/](docs/) for the project overview and component notes.