from __future__ import annotations

import os
from pathlib import Path

from termbench.llm import chat


def main() -> None:
    _load_local_env()
    text_response = chat([{"role": "user", "content": "Say hi in five words"}])
    print(f"text: {text_response.text}")
    print(f"tokens: {text_response.input_tokens} in, {text_response.output_tokens} out")

    tool = {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    }
    tool_response = chat(
        [{"role": "user", "content": "Run the command `echo hello` using the tool"}],
        [tool],
    )
    print(f"tool call: {tool_response.tool_calls}")
    messages = [
        {"role": "user", "content": "Run the command `echo hello` using the tool"},
        tool_response.raw_message,
    ]
    if tool_response.tool_calls:
        call = tool_response.tool_calls[0]
        messages.append({"role": "tool", "tool_call_id": call.id, "content": "hello"})
    final_response = chat(messages, [tool])
    print(f"final: {final_response.text}")


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip("'\""))


if __name__ == "__main__":
    main()