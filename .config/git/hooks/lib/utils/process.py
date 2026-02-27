from __future__ import annotations

import subprocess
from pathlib import Path


def run_cmd(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> tuple[str, str, int]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout, proc.stderr, proc.returncode
