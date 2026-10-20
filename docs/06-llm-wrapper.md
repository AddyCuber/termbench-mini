# 06 — LLM wrapper

## What this is

`llm.py` sends OpenAI-format chat requests through the official OpenAI SDK. Its defaults target Mistral's OpenAI-compatible endpoint, but `BASE_URL`, `API_KEY`, and `MODEL` allow another compatible provider without changing the agent.

The wrapper enforces a request interval, retries temporary failures, and converts provider responses into `LLMResponse` and `ToolCall` dataclasses. API keys are read from the environment and are never printed.

## Why the interface is provider-neutral

The agent only needs text, parsed tool calls, token counts, a finish reason, and the raw assistant message to append to its conversation. It does not need to know which SDK, URL, or response object produced them.

## Three questions you should be able to answer

1. Which configuration values must be pinned for a reproducible run?
2. Which failures are retried, and how does the wrapper avoid retrying ordinary client errors?
3. Why is `raw_message` returned alongside the normalized tool calls?