from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def write_report(results_path: Path, output_path: Path | None = None) -> Path:
    results: list[dict[str, Any]] = json.loads(results_path.read_text(encoding="utf-8"))
    output = output_path or results_path.with_name("report.md")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        groups[(result["task"], result["model"])].append(result)

    lines = [
        "# Termbench report",
        "",
        "| task | model | pass | fail | budget | error | median steps |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (task, model), attempts in sorted(groups.items()):
        outcomes = [item.get("outcome", "pass" if item["passed"] else "fail") for item in attempts]
        steps = [item["steps"] for item in attempts]
        median = statistics.median(steps) if steps else 0
        counts = {outcome: outcomes.count(outcome) for outcome in ("pass", "fail", "budget", "error")}
        lines.append(
            f"| {task} | {model} | {counts['pass']} | {counts['fail']} | "
            f"{counts['budget']} | {counts['error']} | {median} |"
        )

    flagged = []
    for (task, model), attempts in sorted(groups.items()):
        outcomes = [item.get("outcome", "pass" if item["passed"] else "fail") for item in attempts]
        passed = outcomes.count("pass")
        unreliable = outcomes.count("budget") + outcomes.count("error")
        if unreliable >= 2:
            flagged.append(f"- `{task}` with `{model}`: unreliable measurement ({unreliable} budget/error outcomes)")
        elif passed == 0 or (len(attempts) >= 5 and passed == len(attempts)):
            flagged.append(f"- `{task}` with `{model}`: {passed}/{len(attempts)} passes")
    lines.extend(["", "## Check this task"])
    lines.extend(flagged or ["None."])
    failed_attempts = [
        item for item in results if item.get("outcome", "pass" if item["passed"] else "fail") != "pass"
    ]
    if failed_attempts:
        lines.extend(["", "## Failed attempts"])
        for item in failed_attempts:
            test_output = item.get("test_output", "").strip() or "(no verifier output recorded)"
            lines.append(
                f"- `{item['task']}` / `{item['model']}` attempt {item['attempt']} "
                f"({item.get('outcome', 'fail')}): `{test_output}`"
            )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output