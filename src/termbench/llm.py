from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

_DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
_REQUEST_TIMEOUT_S = 60.0
_MAX_TRIES = 5
_last_request_at: float | None = None
_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
    raw_arguments: str | None = None


@dataclass(frozen=True)
class LLMResponse:
    text: str | None
    tool_calls: list[ToolCall]
    input_tokens: int
    output_tokens: int
    finish_reason: str | None
    raw_message: dict[str, Any]


def chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
    """Send one OpenAI-format chat request and normalize its assistant response."""
    base_url = os.environ.get("BASE_URL", _DEFAULT_BASE_URL)
    api_key = _required_env("API_KEY")
    model = _required_model()
    temperature = _float_env("TEMPERATURE", 0.7)
    interval = _float_env("LLM_MIN_INTERVAL_S", 1.1)
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=_REQUEST_TIMEOUT_S, max_retries=0)
    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools is not None:
        request["tools"] = tools
    response = _request_with_retries(client, request, interval)
    choice = response.choices[0]
    message = choice.message
    raw_message = message.model_dump(exclude_none=True)
    tool_calls = [_parse_tool_call(item) for item in (message.tool_calls or [])]
    usage = response.usage
    return LLMResponse(
        text=message.content,
        tool_calls=tool_calls,
        input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
        finish_reason=choice.finish_reason,
        raw_message=raw_message,
    )


def _request_with_retries(client: OpenAI, request: dict[str, Any], interval: float) -> Any:
    for attempt in range(_MAX_TRIES):
        _wait_for_interval(interval)
        try:
            return client.chat.completions.create(**request)
        except (APIConnectionError, APITimeoutError) as exc:
            if attempt == _MAX_TRIES - 1:
                raise RuntimeError(f"LLM request failed after {_MAX_TRIES} tries: {exc}") from exc
            _logger.warning("LLM retry attempt=%d status=connection-error retry_after=None", attempt + 1)
            _sleep_before_retry(attempt, None)
        except APIStatusError as exc:
            status = exc.status_code
            if status != 429 and not 500 <= status <= 599:
                raise RuntimeError(f"LLM request failed with HTTP {status}: {_error_message(exc)}") from exc
            if attempt == _MAX_TRIES - 1:
                raise RuntimeError(f"LLM request failed with HTTP {status}: {_error_message(exc)}") from exc
            retry_after = _retry_after(exc)
            _logger.warning(
                "LLM retry attempt=%d status=%d retry_after=%s",
                attempt + 1,
                status,
                retry_after,
            )
            _sleep_before_retry(attempt, retry_after)
    raise AssertionError("unreachable")


def _parse_tool_call(tool_call: Any) -> ToolCall:
    raw = str(tool_call.function.arguments or "")
    try:
        arguments = json.loads(raw)
    except json.JSONDecodeError:
        return ToolCall(tool_call.id, tool_call.function.name, {}, raw)
    if not isinstance(arguments, dict):
        return ToolCall(tool_call.id, tool_call.function.name, {}, raw)
    return ToolCall(tool_call.id, tool_call.function.name, arguments)


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def _required_model() -> str:
    model = _required_env("MODEL")
    if model.endswith("-latest"):
        raise RuntimeError("MODEL must be pinned; names ending in '-latest' are not allowed")
    return model


def _float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number") from exc
    if parsed < 0:
        raise RuntimeError(f"{name} must not be negative")
    return parsed


def _wait_for_interval(interval: float) -> None:
    global _last_request_at
    if _last_request_at is not None:
        remaining = interval - (time.monotonic() - _last_request_at)
        if remaining > 0:
            time.sleep(remaining)
    _last_request_at = time.monotonic()


def _sleep_before_retry(attempt: int, retry_after: float | None) -> None:
    delay = retry_after if retry_after is not None else (2**attempt) + random.uniform(0, 0.25)
    time.sleep(max(0.0, delay))


def _retry_after(exc: APIStatusError) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) if response is not None else {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
        except (TypeError, ValueError, OverflowError):
            return None


def _error_message(exc: APIStatusError) -> str:
    response = getattr(exc, "response", None)
    try:
        body = response.json() if response is not None else None
    except (AttributeError, ValueError):
        body = None
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
    return str(exc)