from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from termbench.llm import chat
from termbench.sandbox import ExecResult, Sandbox
from termbench.task import Task

_SYSTEM = (
    "You are root in a Linux container. Use the bash tool to complete the task. "
    "Do not install packages or change requested file contents unless the task explicitly requires it; "
    "prefer the smallest direct fix supported by the evidence. "
    "Do not stop until the requested end state is actually working; for service tasks, "
    "start or reload the service and verify a real request to the requested endpoint before stopping. "
    "Reply with a final message and no tool call when finished. Do not mention tests."
)
_BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a bash command in the Linux container.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
}


def run_attempt(
    task: Task,
    sandbox: Sandbox,
    trace_path: Path,
    max_tokens: int = 4096,
) -> tuple[int, int, int, str, str]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": task.prompt},
    ]
    steps = 0
    input_tokens = 0
    output_tokens = 0
    stop_reason = "unknown"
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    with trace_path.open("w", encoding="utf-8") as trace:
        while steps < task.max_steps and input_tokens + output_tokens < max_tokens:
            response = chat(messages, [_BASH_TOOL])
            input_tokens += response.input_tokens
            output_tokens += response.output_tokens
            messages.append(response.raw_message)
            tool_calls = response.tool_calls
            if not tool_calls:
                stop_reason = "finished"
                break

            tool_results: list[dict[str, Any]] = []
            for tool_call in tool_calls:
                steps += 1
                command = str(tool_call.arguments.get("command", ""))
                result = sandbox.exec(command, task.command_timeout_s)
                _write_trace(trace, steps, command, result, input_tokens + output_tokens)
                tool_results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": _tool_output(result),
                    }
                )
            messages.extend(tool_results)

        if stop_reason == "unknown":
            stop_reason = "max_steps" if steps >= task.max_steps else "token_cap"

    return steps, input_tokens, output_tokens, str(trace_path), stop_reason


def _tool_output(result: ExecResult) -> str:
    output = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\nexit_code: {result.exit_code}"
    if len(output) <= 3000:
        return output
    omitted = len(output.encode("utf-8")) - len(output[:1500].encode("utf-8")) - len(output[-1500:].encode("utf-8"))
    return output[:1500] + f"\n[... {omitted} bytes omitted ...]\n" + output[-1500:]


def _write_trace(
    trace: Any,
    step: int,
    command: str,
    result: ExecResult,
    tokens: int,
) -> None:
    record = {
        "step": step,
        "tool": "bash",
        "input": {"command": command},
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "tokens_used": tokens,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    trace.write(json.dumps(record) + "\n")
    trace.flush()