#!/usr/bin/env python3
from __future__ import annotations

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
    print_warning,
)
from lib.utils.file import run_precommit_with_optional_filters  # noqa: E402
from lib.utils.tool import resolve_precommit  # noqa: E402
from lib.runner_interface import RunnerInterface  # noqa: E402


class GlobalPrecommitRunner(RunnerInterface):
    """Runner for global pre-commit checks."""

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

        print_section("🌍 STEP 1/4: Global pre-commit hooks")

        config_path = self.hooks_dir / "configs" / "global-pre-commit-config.yaml"
        if not config_path.is_file():
            print_skip("No global pre-commit config found")
            return 0

        precommit_bin = resolve_precommit(self.env)
        if not precommit_bin:
            print_error("pre-commit not found")
            return 1

        exit_code = run_precommit_with_optional_filters(
            precommit_bin=precommit_bin,
            config_path=str(config_path),
            include_dirs=include_dirs,
            exclude_dirs=exclude_dirs,
            args=self.args,
            env=self.env,
        )

        if exit_code == 10:
            print_skip("No files match include/exclude filters for global hooks")
            return 0
        if exit_code == 0:
            print_success("Global pre-commit passed")
            return 0
        if exit_code == 1:
            print_warning(
                "Global pre-commit completed (some files auto-fixed or minor issues)"
            )
            return 0

        print_error(f"Global pre-commit failed (exit code: {exit_code})")
        return 1


def main() -> int:
    env = dict(__import__("os").environ)
    include_dirs = env.get("PCR_INCLUDE_DIRS", "")
    exclude_dirs = env.get("PCR_EXCLUDE_DIRS", "")
    return GlobalPrecommitRunner(
        HOOKS_DIR,
        sys.argv[1:],
        env,
        include_dirs=include_dirs,
        exclude_dirs=exclude_dirs,
    ).run()


if __name__ == "__main__":
    raise SystemExit(main())
