#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from lib.utils.display import (  # noqa: E402
    CYAN,
    NC,
    print_error,
    print_info,
    print_section,
    print_skip,
    print_success,
    print_warning,
)
from lib.utils.file import (  # noqa: E402
    files_modified,
    git_staged_files,
    restage_files,
    run_precommit_with_optional_filters,
)
from lib.utils.tool import resolve_precommit  # noqa: E402
from lib.runner_interface import RunnerInterface  # noqa: E402

MAX_RETRIES = 2


class LocalPrecommitRunner(RunnerInterface):
    """Runner for local project pre-commit hooks."""

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
        print_section("📁 STEP 3/4: Local project pre-commit hooks")

        local_config = Path(".pre-commit-config.yaml")
        if not local_config.is_file():
            print_skip("No local .pre-commit-config.yaml in this project")
            return 0

        precommit_bin = resolve_precommit(self.env)
        if not precommit_bin:
            print_error("pre-commit not found")
            return 1

        staged_files_before = git_staged_files()
        exit_code = self._run_local_once(precommit_bin, local_config)

        if exit_code == 10:
            print_skip("No files match include/exclude filters for local hooks")
            return 0

        if exit_code == 0:
            print_success("Local pre-commit passed")
            return 0

        if exit_code == 1:
            retry_exit = self._retry_after_auto_fixes(
                precommit_bin,
                local_config,
                staged_files_before,
            )
            if retry_exit == 0:
                return 0
            if retry_exit == 1:
                print_warning("Local pre-commit completed with warnings")
                return 0
            exit_code = retry_exit

        print_error(f"Local pre-commit failed (exit code: {exit_code})")
        return 1

    def _run_local_once(self, precommit_bin: str, local_config: Path) -> int:
        return run_precommit_with_optional_filters(
            precommit_bin=precommit_bin,
            config_path=str(local_config),
            include_dirs=self.include_dirs,
            exclude_dirs=self.exclude_dirs,
            args=self.args,
            env=self.env,
        )

    def _modified_staged_files(self, staged_files: list[str]) -> list[str]:
        changed: list[str] = []
        for file in staged_files:
            if not Path(file).is_file():
                continue
            if (
                subprocess.run(["git", "diff", "--quiet", file], check=False).returncode
                != 0
            ):
                changed.append(file)
        return changed

    def _retry_after_auto_fixes(
        self,
        precommit_bin: str,
        local_config: Path,
        staged_files_before: list[str],
    ) -> int:
        if not files_modified(staged_files_before):
            return 1

        messages = [
            "Auto-fixes detected. Re-staging modified files...",
            "More auto-fixes detected. Re-staging again...",
        ]
        success_messages = [
            "Local pre-commit passed after auto-fixes",
            "Local pre-commit passed after second round of auto-fixes",
        ]

        exit_code = 1
        for attempt in range(2, MAX_RETRIES + 2):
            message_index = attempt - 2
            print_info(messages[message_index])

            modified_files = self._modified_staged_files(staged_files_before)
            if modified_files:
                print(f"{CYAN}Modified files:{NC}")
                for file in modified_files:
                    print(f"  - {file}")

            restage_files(staged_files_before)

            print_info(f"Retrying pre-commit (attempt {attempt}/{MAX_RETRIES + 1})...")
            exit_code = self._run_local_once(precommit_bin, local_config)
            if exit_code == 0:
                print_success(success_messages[message_index])
                return 0
            if exit_code != 1 or not files_modified(staged_files_before):
                return exit_code

        return exit_code


def main() -> int:
    env = dict(__import__("os").environ)
    include_dirs = env.get("PCR_INCLUDE_DIRS", "")
    exclude_dirs = env.get("PCR_EXCLUDE_DIRS", "")
    return LocalPrecommitRunner(
        HOOKS_DIR,
        sys.argv[1:],
        env,
        include_dirs=include_dirs,
        exclude_dirs=exclude_dirs,
    ).run()


if __name__ == "__main__":
    raise SystemExit(main())
