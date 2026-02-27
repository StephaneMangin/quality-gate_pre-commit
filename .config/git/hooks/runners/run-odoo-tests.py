#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from lib.utils.display import (  # noqa: E402
    print_error,
    print_info,
    print_section,
    print_skip,
    print_success,
)
from lib.utils.odoo import changed_modules, is_manifest_project  # noqa: E402
from lib.runner_interface import RunnerInterface  # noqa: E402


class OdooTestsRunner(RunnerInterface):
    """Runner for Odoo module tests step."""

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
        self.env["QUALITY_GATE_INCLUDE_DIRS"] = self.include_dirs
        self.env["QUALITY_GATE_EXCLUDE_DIRS"] = self.exclude_dirs
        print_section("🧪 STEP 4/4: Module tests")

        if not is_manifest_project(self.include_dirs, self.exclude_dirs):
            print_skip("No manifest-based modules detected")
            return 0

        check_cmd = "source ~/.odoo_functions 2>/dev/null || true; type -t odootest >/dev/null 2>&1"
        if (
            subprocess.run(
                ["bash", "-lc", check_cmd], env=self.env, check=False
            ).returncode
            != 0
        ):
            print_skip("odootest not available")
            return 0

        modules = changed_modules(self.include_dirs, self.exclude_dirs)
        if not modules:
            print_skip("No changed modules to test")
            return 0

        modules_str = " ".join(modules)
        print_info(f"Testing modules: {modules_str}")

        test_cmd = (
            f"source ~/.odoo_functions 2>/dev/null || true; odootest -op {modules_str}"
        )
        proc = subprocess.run(
            ["bash", "-lc", test_cmd],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

        output = (proc.stdout or "") + (proc.stderr or "")
        if output.strip():
            print(output, end="" if output.endswith("\n") else "\n")

        if proc.returncode == 0:
            print_success("Module tests passed for all modules")
            return 0

        if re.search(
            r"(odoo(-bin)?|/odoo)[^\n\r]*(not found|command not found|introuvable)",
            output,
            re.IGNORECASE,
        ):
            print_skip("odoo not found in environment, skipping module tests")
            return 0

        print_error(f"Module tests failed (exit code: {proc.returncode})")
        return 1


def main() -> int:
    env = dict(__import__("os").environ)
    include_dirs = env.get("QUALITY_GATE_INCLUDE_DIRS") or env.get(
        "PCR_INCLUDE_DIRS", ""
    )
    exclude_dirs = env.get("QUALITY_GATE_EXCLUDE_DIRS") or env.get(
        "PCR_EXCLUDE_DIRS", ""
    )
    return OdooTestsRunner(
        HOOKS_DIR,
        sys.argv[1:],
        env,
        include_dirs=include_dirs,
        exclude_dirs=exclude_dirs,
    ).run()


if __name__ == "__main__":
    raise SystemExit(main())
