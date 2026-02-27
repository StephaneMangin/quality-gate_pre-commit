from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

from .display import iter_with_progress as display_iter_with_progress
from .file import collect_files, collect_python_files
from .path import (
    ALWAYS_EXCLUDED_DIRS,
    PYTHON_SOURCE_DIRS,
    env_include_exclude_dirs,
    expand_allowed_targets,
    filter_paths_with_env_dirs,
    is_path_allowed,
    parse_dir_csv_env,
)
from .process import run_cmd
from .tool import get_venv_bin_dir


def ensure_tools_installed(repo_root: Path) -> None:
    required_tools = {
        "radon": "radon",
        "vulture": "vulture",
        "coverage": "coverage",
    }

    missing: list[str] = []
    venv_bin = get_venv_bin_dir(repo_root)

    for module_name, pip_name in required_tools.items():
        if venv_bin:
            tool_path = venv_bin / module_name
            if tool_path.exists():
                continue

        if shutil.which(module_name):
            continue

        if importlib.util.find_spec(module_name) is not None:
            continue

        missing.append(pip_name)

    if not missing:
        return

    print(f"[quality-gate] ⚠ Missing tools: {', '.join(missing)}", file=sys.stderr)
    print(
        "[quality-gate]   Please install them in your environment (venv/mise/pipx/global):",
        file=sys.stderr,
    )
    print(f"[quality-gate]   pip install {' '.join(missing)}", file=sys.stderr)
    print(
        "[quality-gate]   (Checks for missing tools will be skipped)", file=sys.stderr
    )


def detect_python_project(repo_root: Path, staged: list[Path]) -> bool:
    markers = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "tox.ini"]
    if any((repo_root / marker).exists() for marker in markers):
        return True
    if any(path.suffix == ".py" for path in staged):
        return True
    return bool(collect_python_files(repo_root, include_hidden=True))


def staged_files(repo_root: Path) -> list[Path]:
    out, _, rc = run_cmd(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
        repo_root,
    )
    if rc != 0:
        return []
    return [repo_root / line.strip() for line in out.splitlines() if line.strip()]


def vulture_exclude_csv() -> str:
    _, exclude_dirs = env_include_exclude_dirs()
    merged: list[str] = []
    seen: set[str] = set()

    for value in [*sorted(ALWAYS_EXCLUDED_DIRS), *exclude_dirs]:
        normalized = value.rstrip("/")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(normalized)

    return ",".join(merged)


def iter_python_targets(repo_root: Path, staged: list[Path]) -> list[str]:
    include_dirs = parse_dir_csv_env("QUALITY_GATE_INCLUDE_DIRS")
    exclude_dirs = parse_dir_csv_env("QUALITY_GATE_EXCLUDE_DIRS")

    targets: list[Path] = []
    for dirname in PYTHON_SOURCE_DIRS:
        candidate = repo_root / dirname
        if candidate.exists():
            targets.extend(
                expand_allowed_targets(candidate, repo_root, include_dirs, exclude_dirs)
            )

    staged_py = [path for path in staged if path.suffix == ".py" and path.exists()]
    targets.extend(
        path
        for path in staged_py
        if "tests" not in path.parts
        and is_path_allowed(path, repo_root, include_dirs, exclude_dirs)
    )

    if include_dirs and not targets:
        for directory in include_dirs:
            candidate = repo_root / directory
            if candidate.exists():
                targets.extend(
                    expand_allowed_targets(
                        candidate, repo_root, include_dirs, exclude_dirs
                    )
                )

    if not targets:
        for candidate in repo_root.iterdir():
            targets.extend(
                expand_allowed_targets(
                    candidate,
                    repo_root,
                    include_dirs if include_dirs else [],
                    exclude_dirs if exclude_dirs else [],
                )
            )

    if not targets:
        targets = [repo_root]

    dedup: list[str] = []
    seen = set()
    for path in targets:
        value = str(path.relative_to(repo_root)) if path != repo_root else "."
        if value not in seen:
            dedup.append(value)
            seen.add(value)
    return dedup


def iter_with_progress(
    files: list[Path],
    repo_root: Path,
    enabled: bool,
    prefix: str,
    every: int,
):
    yield from display_iter_with_progress(files, repo_root, enabled, prefix, every)


def detect_python_sources(repo_root: Path) -> list[str]:
    sources: list[str] = []
    include_dirs, exclude_dirs = env_include_exclude_dirs()

    for dirname in PYTHON_SOURCE_DIRS:
        candidate = repo_root / dirname
        if not candidate.is_dir():
            continue

        expanded = expand_allowed_targets(candidate, repo_root, include_dirs, exclude_dirs)
        for path in expanded:
            if not path.is_dir():
                continue
            if is_path_allowed(path, repo_root, include_dirs, exclude_dirs):
                sources.append(str(path.relative_to(repo_root)))

    manifest_dirs: set[str] = set()
    manifest_count_at_root = 0

    manifest_files = collect_files(
        repo_root,
        patterns=["__manifest__.py"],
        include_hidden=False,
    )
    manifest_files = filter_paths_with_env_dirs(manifest_files, repo_root)

    for manifest in manifest_files:
        addon_dir = manifest.parent
        if addon_dir.parent == repo_root:
            manifest_count_at_root += 1
        else:
            relative = addon_dir.parent.relative_to(repo_root)
            manifest_dirs.add(str(relative))

    if manifest_count_at_root >= 2:
        sources.append(".")
    elif manifest_dirs:
        sources.extend(sorted(manifest_dirs))

    if not sources:
        py_files = collect_python_files(repo_root, include_hidden=True)
        if any("setup" not in py_file.name.lower() for py_file in py_files):
            sources.append(".")

    return list(dict.fromkeys(sources))
