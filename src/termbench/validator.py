from __future__ import annotations

import subprocess
from dataclasses import dataclass

from termbench.sandbox import ExecResult, Sandbox
from termbench.task import Task, load_task

_FLAKE_RUNS = 3
_FIND_LEAKS = (
    "find / \\( -path '*/tests/test.sh' -o -path '*/solution/solve.sh' \\) "
    "2>/dev/null"
)
_NETWORK_PROBE = "curl -s --max-time 3 https://example.com"


@dataclass(frozen=True)
class Check:
    number: int
    name: str
    ok: bool
    reason: str


def image_name(task: Task) -> str:
    return f"termbench-{task.id}"


def build_image(task: Task) -> str:
    image, ok, reason = _build(task)
    if not ok:
        raise RuntimeError(reason)
    return image


def validate(task_id: str) -> int:
    task = load_task(task_id)
    checks: list[Check] = []

    checks.append(_check_forbidden(task))

    image, built, build_reason = _build(task)
    checks.append(Check(1, "Builds cleanly", built, build_reason))

    if built:
        checks.extend(_check_image_hygiene(image))
        checks.extend(_check_fail_pass_and_flake(task, image))
    else:
        checks.append(Check(2, "Tests FAIL on the untouched environment", False, "skipped (build failed)"))
        checks.append(Check(3, "Tests PASS after solve.sh", False, "skipped (build failed)"))
        checks.append(Check(4, "Fail/pass identical across 3 fresh containers", False, "skipped (build failed)"))
        checks.append(Check(5, "tests/ and solution/ absent from image", False, "skipped (build failed)"))
        checks.append(Check(7, "No network inside container", False, "skipped (build failed)"))

    checks.sort(key=lambda c: c.number)
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"{status}: {check.number}. {check.name} ({check.reason})")
    _print_table(checks)
    return 0 if all(c.ok for c in checks) else 1


def _build(task: Task) -> tuple[str, bool, str]:
    image = image_name(task)
    proc = subprocess.run(
        ["docker", "build", "-t", image, str(task.environment_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode == 0:
        return image, True, "docker build exit 0"
    tail = (proc.stderr or proc.stdout).strip()[-300:]
    return image, False, f"docker build exit {proc.returncode}: {tail}"


def _check_forbidden(task: Task) -> Check:
    hits = [s for s in task.forbidden_in_prompt if s and s in task.prompt]
    if hits:
        return Check(
            6,
            "forbidden_in_prompt absent from prompt",
            False,
            "leaked: " + ", ".join(repr(h) for h in hits),
        )
    return Check(
        6,
        "forbidden_in_prompt absent from prompt",
        True,
        "none of the forbidden strings appear",
    )


def _check_image_hygiene(image: str) -> list[Check]:
    with Sandbox(image) as box:
        leaked = box.exec(_FIND_LEAKS, timeout=30)
        paths = [ln.strip() for ln in leaked.stdout.splitlines() if ln.strip()]
        probe = box.exec(_NETWORK_PROBE, timeout=10)

    leak_ok = not paths
    leak_reason = (
        "no */tests/test.sh or */solution/solve.sh"
        if leak_ok
        else "found: " + ", ".join(paths[:8])
    )
    net_ok = probe.exit_code != 0
    net_reason = (
        f"curl to example.com exited {probe.exit_code}"
        if net_ok
        else "curl to example.com succeeded (network not isolated)"
    )
    return [
        Check(5, "tests/ and solution/ absent from image", leak_ok, leak_reason),
        Check(7, "No network inside container", net_ok, net_reason),
    ]


def _check_fail_pass_and_flake(task: Task, image: str) -> list[Check]:
    pairs: list[tuple[int, int]] = []
    notes: list[str] = []
    for i in range(_FLAKE_RUNS):
        before, after, note = _one_fail_then_pass(task, image)
        pairs.append((before, after))
        if note:
            notes.append(f"run {i + 1}: {note}")

    fail_ok = all(before != 0 for before, _ in pairs)
    pass_ok = all(after == 0 for _, after in pairs) and not notes
    identical = len(set(pairs)) == 1

    if fail_ok:
        fail_reason = f"{_FLAKE_RUNS}/{_FLAKE_RUNS} untouched runs failed"
    else:
        fail_reason = "untouched tests passed on a run: " + ", ".join(
            f"{b}/{a}" for b, a in pairs
        )

    if pass_ok:
        pass_reason = f"{_FLAKE_RUNS}/{_FLAKE_RUNS} passed after solve.sh"
    elif notes:
        pass_reason = "; ".join(notes)
    else:
        pass_reason = "post-solve exits: " + ", ".join(str(a) for _, a in pairs)

    flake_reason = (
        f"all {_FLAKE_RUNS} containers got before={pairs[0][0]} after={pairs[0][1]}"
        if identical
        else "results differed: " + ", ".join(f"{b}/{a}" for b, a in pairs)
    )
    if notes:
        flake_reason += " (" + "; ".join(notes) + ")"

    return [
        Check(2, "Tests FAIL on the untouched environment", fail_ok, fail_reason),
        Check(3, "Tests PASS after solve.sh", pass_ok, pass_reason),
        Check(4, "Fail/pass identical across 3 fresh containers", identical, flake_reason),
    ]


def _one_fail_then_pass(task: Task, image: str) -> tuple[int, int, str]:
    with Sandbox(image) as box:
        before = box.run_tests(task.tests_dir, task.verify_timeout_s)
        box.copy_in(task.solution_dir, "/tmp/termbench-solution")
        solved = box.exec(
            "bash /tmp/termbench-solution/solve.sh",
            task.command_timeout_s,
        )
        if solved.exit_code != 0:
            detail = solved.stderr.strip() or solved.stdout.strip() or f"exit {solved.exit_code}"
            return before.exit_code, solved.exit_code, f"solve.sh failed: {detail}"
        after: ExecResult = box.run_tests(task.tests_dir, task.verify_timeout_s)
        return before.exit_code, after.exit_code, ""


def _print_table(checks: list[Check]) -> None:
    print()
    print(f"{'#':<3} {'result':<6} check")
    print(f"{'-':<3} {'------':<6} -----")
    for check in checks:
        result = "PASS" if check.ok else "FAIL"
        print(f"{check.number:<3} {result:<6} {check.name}")
    passed = sum(1 for c in checks if c.ok)
    print(f"{passed}/{len(checks)} passed")
