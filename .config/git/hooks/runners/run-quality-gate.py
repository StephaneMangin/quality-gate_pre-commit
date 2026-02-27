#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from lib.utils.display import (  # noqa: E402
    print_error,
    print_section,
    print_skip,
    print_success,
)
from lib.utils.tool import resolve_python  # noqa: E402
from lib.runner_interface import RunnerInterface  # noqa: E402


class QualityGateRunner(RunnerInterface):
    """Runner for quality gate step."""

    def __init__(
        self,
        hooks_dir: Path,
        args: list[str],
        env: dict[str, str],
        *,
        include_dirs: str,
        exclude_dirs: str,
    ) -> None:
        super().__init__(
            hooks_dir,
            args,
            env,
            include_dirs=include_dirs,
            exclude_dirs=exclude_dirs,
        )

    def run(self) -> int:
        include_dirs = self.include_dirs
        exclude_dirs = self.exclude_dirs
        self.env["QUALITY_GATE_INCLUDE_DIRS"] = include_dirs
        self.env["QUALITY_GATE_EXCLUDE_DIRS"] = exclude_dirs

        print_section("🔍 STEP 2/4: Quality gate")

        script = self.hooks_dir / "quality_gate" / "__main__.py"
        if not script.is_file():
            print_skip("Quality gate script not found")
            return 0

        python_bin = resolve_python(self.env)
        if not python_bin:
            print_skip("Python not found, skipping quality gate")
            return 0

        proc = subprocess.Popen(
            [python_bin, str(script)],
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")

        exit_code = proc.wait()
        print()

        if exit_code == 0:
            print_success("Quality gate passed")
            return 0

        print_error(f"Quality gate failed (exit code: {exit_code})")
        return 1


def main() -> int:
    env = dict(__import__("os").environ)
    include_dirs = env.get("QUALITY_GATE_INCLUDE_DIRS") or env.get(
        "PCR_INCLUDE_DIRS", ""
    )
    exclude_dirs = env.get("QUALITY_GATE_EXCLUDE_DIRS") or env.get(
        "PCR_EXCLUDE_DIRS", ""
    )
    return QualityGateRunner(
        HOOKS_DIR,
        sys.argv[1:],
        env,
        include_dirs=include_dirs,
        exclude_dirs=exclude_dirs,
    ).run()


if __name__ == "__main__":
    raise SystemExit(main())
