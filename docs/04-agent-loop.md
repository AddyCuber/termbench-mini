# 04 — Agent loop

## What this is

The agent loop gives a model one `bash` tool inside a fresh task container. It records each command and its result, then runs the hidden verifier only after the model stops.

## How data flows

1. `termbench run` loads the task and builds only its `environment/` directory.
2. `Sandbox` starts the image with no network and keeps it alive with `sleep infinity`.
3. `agent.py` sends the task prompt through the provider-neutral `chat()` interface, executes each `bash` tool call, and sends stdout, stderr, and the exit code back to the model.
4. Each tool call is appended to `runs/<run_id>/<task>/<model>/attempt_N.jsonl`.
5. After the loop ends, the hidden tests are copied into the container and run. The process exits 0 only when they pass.

## Three questions you should be able to answer

1. Why are hidden tests copied in only after the model loop ends?
2. What stops the loop if the model keeps requesting commands?
3. Which environment variable supplies the key for the selected provider?

The provider request timeout defaults to 300 seconds and can be changed with `--llm-timeout` for a single run.

Gemini thinking is controlled with `GEMINI_THINKING_BUDGET`; `0` is appropriate for short, repeatable terminal benchmark attempts.