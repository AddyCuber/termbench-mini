from __future__ import annotations

import subprocess
from pathlib import Path
from types import TracebackType
from typing import NamedTuple

class ExecResult(NamedTuple):
    stdout: str
    stderr: str
    exit_code: int


class Sandbox:
    """Isolated container: no network, no mounts, always removed on exit."""

    def __init__(self, image: str) -> None:
        self.image = image
        self.container_id: str | None = None

    def __enter__(self) -> Sandbox:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.stop()

    def start(self) -> None:
        if self.container_id is not None:
            raise RuntimeError("sandbox already started")
        proc = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--network",
                "none",
                "--memory",
                "1g",
                "--cpus",
                "1",
                self.image,
                "sleep",
                "infinity",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"docker run failed: {proc.stderr.strip()}")
        self.container_id = proc.stdout.strip()

    def stop(self) -> None:
        cid = self.container_id
        self.container_id = None
        if not cid:
            return
        subprocess.run(
            ["docker", "rm", "-f", cid],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def exec(self, cmd: str, timeout: int) -> ExecResult:
        cid = self._require_id()
        try:
            proc = subprocess.run(
                ["docker", "exec", cid, "bash", "-c", cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            out = _as_text(exc.stdout)
            err = _as_text(exc.stderr)
            if err:
                err = err + "\n"
            return ExecResult(out, err + "command timed out", 124)
        return ExecResult(proc.stdout, proc.stderr, proc.returncode)

    def copy_in(self, src: Path, dst: str) -> None:
        cid = self._require_id()
        src = src.resolve()
        if src.is_dir():
            # docker cp dir/. requires the destination to already exist
            mkdir = self.exec(f"rm -rf {dst} && mkdir -p {dst}", timeout=15)
            if mkdir.exit_code != 0:
                raise RuntimeError(f"mkdir {dst} failed: {mkdir.stderr}")
            host = str(src) + "/."
        else:
            parent = str(Path(dst).parent)
            mkdir = self.exec(f"mkdir -p {parent}", timeout=15)
            if mkdir.exit_code != 0:
                raise RuntimeError(f"mkdir {parent} failed: {mkdir.stderr}")
            host = str(src)
        proc = subprocess.run(
            ["docker", "cp", host, f"{cid}:{dst}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"docker cp failed: {proc.stderr.strip()}")

    def run_tests(self, tests_dir: Path, timeout: int) -> ExecResult:
        self.copy_in(tests_dir, "/tmp/termbench-tests")
        return self.exec("bash /tmp/termbench-tests/test.sh", timeout)

    def _require_id(self) -> str:
        if self.container_id is None:
            raise RuntimeError("sandbox is not started")
        return self.container_id


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value
