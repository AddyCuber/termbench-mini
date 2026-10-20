from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from termbench.agent import run_attempt
from termbench.sandbox import Sandbox
from termbench.task import Task, load_task, repo_root
from termbench.validator import build_image


def run_batch(
    task_ids: list[str],
    models: list[str],
    attempts: int,
    max_tokens: int,
    max_total_tokens: int | None,
) -> tuple[Path, int]:
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = repo_root() / "runs" / run_id
    results_path = run_dir / "results.json"
    results: list[dict[str, Any]] = []
    total_tokens = 0
    stopped = False

    for task_id in task_ids:
        task = load_task(task_id)
        image = build_image(task)
        for model in models:
            for attempt in range(1, attempts + 1):
                if max_total_tokens is not None and total_tokens >= max_total_tokens:
                    stopped = True
                    break
                result = _run_one(
                    task,
                    image,
                    model,
                    attempt,
                    max_tokens,
                    run_dir,
                )
                results.append(result)
                total_tokens += int(result["input_tokens"]) + int(result["output_tokens"])
                _write_results(results_path, results)
                print(
                    f"{task.id} {model} attempt {attempt}: "
                    f"{'PASS' if result['passed'] else 'FAIL'}"
                )
            if stopped:
                break
        if stopped:
            break

    _write_results(results_path, results)
    if stopped:
        print(f"stopped: max total tokens reached ({total_tokens})")
    print(f"results: {results_path}")
    return results_path, 0 if results and not stopped else (0 if stopped else 1)


def _run_one(
    task: Task,
    image: str,
    model: str,
    attempt: int,
    max_tokens: int,
    run_dir: Path,
) -> dict[str, Any]:
    started = datetime.now(UTC)
    trace_path = run_dir / task.id / _safe_name(model) / f"attempt_{attempt}.jsonl"
    steps = 0
    input_tokens = 0
    output_tokens = 0
    passed = False
    error = ""
    test_output = ""
    previous_model = os.environ.get("MODEL")
    os.environ["MODEL"] = model
    try:
        with Sandbox(image) as sandbox:
            steps, input_tokens, output_tokens, trace, stop_reason = run_attempt(
                task,
                sandbox,
                trace_path,
                max_tokens,
            )
            verify = sandbox.run_tests(task.tests_dir, task.verify_timeout_s)
            passed = verify.exit_code == 0
            test_output = _result_output(verify)
    except (RuntimeError, OSError) as exc:
        error = str(exc)
        trace = str(trace_path)
        stop_reason = "error"
    finally:
        if previous_model is None:
            os.environ.pop("MODEL", None)
        else:
            os.environ["MODEL"] = previous_model
    finished = datetime.now(UTC)
    return {
        "task": task.id,
        "model": model,
        "attempt": attempt,
        "passed": passed,
        "stop_reason": stop_reason,
        "outcome": _outcome(passed, stop_reason),
        "steps": steps,
        "wall_seconds": (finished - started).total_seconds(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "trace_path": trace,
        "error": error,
        "test_output": test_output[-1000:],
    }


def _write_results(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _outcome(passed: bool, stop_reason: str) -> str:
    if passed:
        return "pass"
    if stop_reason == "error":
        return "error"
    if stop_reason == "token_cap":
        return "budget"
    return "fail"


def _result_output(result: Any) -> str:
    return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"[-1000:]