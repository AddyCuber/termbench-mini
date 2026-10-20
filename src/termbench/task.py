from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]


def repo_root() -> Path:
    return _REPO_ROOT


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    prompt: str
    max_steps: int
    command_timeout_s: int
    verify_timeout_s: int
    forbidden_in_prompt: list[str]
    notes: str
    root: Path

    @property
    def environment_dir(self) -> Path:
        return self.root / "environment"

    @property
    def tests_dir(self) -> Path:
        return self.root / "tests"

    @property
    def solution_dir(self) -> Path:
        return self.root / "solution"


def load_task(task_id: str, tasks_root: Path | None = None) -> Task:
    root = _find_task_dir(tasks_root or (repo_root() / "tasks"), task_id)
    data = yaml.safe_load((root / "task.yaml").read_text(encoding="utf-8"))
    return Task(
        id=data["id"],
        title=data["title"],
        prompt=data["prompt"],
        max_steps=int(data["max_steps"]),
        command_timeout_s=int(data["command_timeout_s"]),
        verify_timeout_s=int(data["verify_timeout_s"]),
        forbidden_in_prompt=list(data.get("forbidden_in_prompt") or []),
        notes=str(data.get("notes") or ""),
        root=root,
    )


def _find_task_dir(tasks_root: Path, task_id: str) -> Path:
    exact = tasks_root / task_id
    if (exact / "task.yaml").is_file():
        return exact
    matches = sorted(
        p for p in tasks_root.glob(f"{task_id}*") if (p / "task.yaml").is_file()
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"no task matching {task_id!r} under {tasks_root}")
    names = ", ".join(p.name for p in matches)
    raise ValueError(f"ambiguous task id {task_id!r}: {names}")
