from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from termbench.agent import run_attempt
from termbench.report import write_report
from termbench.runner import run_batch
from termbench.sandbox import Sandbox
from termbench.task import load_task, repo_root
from termbench.validator import validate
from termbench.validator import build_image


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="termbench")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser(
        "validate",
        help="build a task image and check tests fail, then pass after solve.sh",
    )
    p_validate.add_argument("task_id", help="task id or prefix, e.g. 001")

    p_run = sub.add_parser("run", help="run one model attempt in a task sandbox")
    p_run.add_argument("task_id", help="task id or prefix, e.g. 001")
    p_run.add_argument("--model", default=os.environ.get("MODEL"))
    p_run.add_argument("--attempt", type=int, default=1)
    p_run.add_argument("--max-tokens", type=int, default=4096)

    p_batch = sub.add_parser("batch", help="run repeated attempts and save results")
    p_batch.add_argument("--tasks", required=True, help="all or comma-separated task ids")
    p_batch.add_argument("--models", required=True, help="comma-separated model names")
    p_batch.add_argument("--attempts", type=int, default=1)
    p_batch.add_argument("--max-tokens", type=int, default=4096)
    p_batch.add_argument("--max-total-tokens", type=int)

    p_report = sub.add_parser("report", help="write report.md from results.json")
    p_report.add_argument("results", type=Path)
    p_report.add_argument("--output", type=Path)

    args = parser.parse_args(argv)
    if args.command == "validate":
        raise SystemExit(validate(args.task_id))
    if args.command == "run":
        raise SystemExit(_run(args))
    if args.command == "batch":
        raise SystemExit(_batch(args))
    if args.command == "report":
        print(f"report: {write_report(args.results, args.output)}")
        raise SystemExit(0)
    raise SystemExit(f"unknown command: {args.command}")


def _run(args: argparse.Namespace) -> int:
    if not args.model:
        raise SystemExit("--model or MODEL is required")
    task = load_task(args.task_id)
    image = build_image(task)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    trace = repo_root() / "runs" / run_id / task.id / args.model / f"attempt_{args.attempt}.jsonl"
    previous_model = os.environ.get("MODEL")
    os.environ["MODEL"] = args.model
    try:
        with Sandbox(image) as sandbox:
            steps, input_tokens, output_tokens, trace_path, stop_reason = run_attempt(
                task,
                sandbox,
                trace,
                args.max_tokens,
            )
            result = sandbox.run_tests(task.tests_dir, task.verify_timeout_s)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        if previous_model is None:
            os.environ.pop("MODEL", None)
        else:
            os.environ["MODEL"] = previous_model
    passed = result.exit_code == 0
    print(f"{'PASS' if passed else 'FAIL'}: attempt {args.attempt}")
    print(f"steps: {steps}")
    print(f"input tokens: {input_tokens}")
    print(f"output tokens: {output_tokens}")
    print(f"stop reason: {stop_reason}")
    print(f"trace: {trace_path}")
    return 0 if passed else 1


def _batch(args: argparse.Namespace) -> int:
    if args.attempts < 1:
        raise SystemExit("--attempts must be at least 1")
    task_ids = _task_ids(args.tasks)
    models = [model.strip() for model in args.models.split(",") if model.strip()]
    if not models:
        raise SystemExit("--models must contain at least one model")
    _, exit_code = run_batch(
        task_ids,
        models,
        args.attempts,
        args.max_tokens,
        args.max_total_tokens,
    )
    return exit_code


def _task_ids(value: str) -> list[str]:
    if value != "all":
        return [item.strip() for item in value.split(",") if item.strip()]
    tasks_dir = repo_root() / "tasks"
    return sorted(path.name for path in tasks_dir.iterdir() if (path / "task.yaml").is_file())


if __name__ == "__main__":
    main(sys.argv[1:])
