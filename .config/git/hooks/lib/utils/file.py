from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .path import ALWAYS_EXCLUDED_DIRS, is_excluded_by_dirs
from .process import run_cmd


def git_tracked_files() -> list[str]:
    out, _, rc = run_cmd(["git", "ls-files"], Path.cwd())
    if rc != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def git_staged_files() -> list[str]:
    out, _, rc = run_cmd(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
        Path.cwd(),
    )
    if rc != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def files_modified(files: list[str]) -> bool:
    for file in files:
        if not Path(file).is_file():
            continue
        _, _, rc = run_cmd(["git", "diff", "--quiet", "--", file], Path.cwd())
        if rc != 0:
            return True
    return False


def restage_files(files: list[str]) -> None:
    if not files:
        return
    run_cmd(["git", "add", *files], Path.cwd())


def run_precommit_with_optional_filters(
    precommit_bin: str,
    config_path: str,
    include_dirs: str,
    exclude_dirs: str,
    args: list[str],
    env: dict[str, str],
) -> int:
    from .path import build_filtered_file_list, strip_all_files_args

    if include_dirs or exclude_dirs:
        filtered_files = build_filtered_file_list(include_dirs, exclude_dirs)
        filtered_args = strip_all_files_args(args)

        if not filtered_files:
            return 10

        cmd = [
            precommit_bin,
            "run",
            "--config",
            config_path,
            *filtered_args,
            "--files",
            *filtered_files,
        ]
        _, _, rc = run_cmd(cmd, Path.cwd(), env=env)
        return rc

    cmd = [precommit_bin, "run", "--config", config_path, *args]
    _, _, rc = run_cmd(cmd, Path.cwd(), env=env)
    return rc


def collect_files(
    root_dir: Path,
    patterns: Iterable[str],
    exclude_dirs: set[str] | None = None,
    include_hidden: bool = False,
) -> list[Path]:
    exclude_dirs = exclude_dirs or ALWAYS_EXCLUDED_DIRS

    found: list[Path] = []
    seen: set[Path] = set()

    for pattern in patterns:
        for path in root_dir.rglob(pattern):
            if not path.is_file():
                continue

            rel_parts = path.relative_to(root_dir).parts
            if is_excluded_by_dirs(path, root_dir, set(exclude_dirs)):
                continue

            if not include_hidden and any(part.startswith(".") for part in rel_parts):
                continue

            if path in seen:
                continue
            seen.add(path)
            found.append(path)

    return sorted(found)


def collect_python_files(repo_root: Path, include_hidden: bool = True) -> list[Path]:
    from .path import filter_paths_with_env_dirs

    py_files = collect_files(
        repo_root,
        patterns=["*.py"],
        exclude_dirs=ALWAYS_EXCLUDED_DIRS,
        include_hidden=include_hidden,
    )
    return filter_paths_with_env_dirs(py_files, repo_root)
