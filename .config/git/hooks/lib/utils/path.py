from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def _normalize_csv_token(token: str) -> str:
    value = token.strip()
    if value.startswith("./"):
        value = value[2:]
    return value.rstrip("/")


def _csv_unique(*values: str) -> str:
    seen: set[str] = set()
    merged: list[str] = []
    for value in values:
        for token in value.split(","):
            item = _normalize_csv_token(token)
            if not item:
                continue
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return ",".join(merged)


def csv_dirs(csv: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()

    for token in csv.split(","):
        value = _normalize_csv_token(token)
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def match_dir_prefix(path: str, directory: str) -> bool:
    if directory in {"", "."}:
        return True
    return path == directory or path.startswith(f"{directory}/")


def parse_dir_csv_env(var_name: str) -> list[str]:
    return csv_dirs(os.getenv(var_name, ""))


def env_include_exclude_dirs() -> tuple[list[str], list[str]]:
    include_dirs = parse_dir_csv_env("QUALITY_GATE_INCLUDE_DIRS")
    exclude_dirs = parse_dir_csv_env("QUALITY_GATE_EXCLUDE_DIRS")
    return include_dirs, exclude_dirs


def relative_parts_and_value(path: Path, repo_root: Path) -> tuple[Path, str]:
    try:
        relative_path = path.relative_to(repo_root)
        relative = str(relative_path)
    except ValueError:
        relative_path = path
        relative = str(path)

    if relative.startswith("./"):
        relative = relative[2:]
    return relative_path, relative

VENV_DIR_NAMES = (".venv", "venv", ".env")
PYTHON_SOURCE_DIRS = ("src", "app")
MODULE_SEARCH_DIRS = ("src", "addons", "modules", "odoo")
ALWAYS_EXCLUDED_DIRS = {
    ".github",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "src/odoo",
    "src/odoo-enterprise",
    "src/addons",
}


def is_excluded_by_dirs(path: Path, repo_root: Path, excludes: set[str]) -> bool:
    relative_path, relative = relative_parts_and_value(path, repo_root)

    for excluded in excludes:
        normalized = excluded.strip().rstrip("/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        if not normalized:
            continue

        if "/" in normalized:
            if match_dir_prefix(relative, normalized):
                return True
            continue

        if normalized in relative_path.parts:
            return True

    return False


def is_path_allowed(path: Path, repo_root: Path, includes: list[str], excludes: list[str]) -> bool:
    _, relative = relative_parts_and_value(path, repo_root)

    if is_excluded_by_dirs(path, repo_root, ALWAYS_EXCLUDED_DIRS):
        return False

    if any(match_dir_prefix(relative, excluded) for excluded in excludes):
        return False
    if includes and not any(match_dir_prefix(relative, included) for included in includes):
        return False
    return True


def is_path_filtered_out(path: str, include_csv: str, exclude_csv: str) -> bool:
    include_dirs = csv_dirs(include_csv) if include_csv else []
    exclude_dirs = csv_dirs(exclude_csv) if exclude_csv else []

    include_ok = True
    if include_dirs:
        include_ok = any(match_dir_prefix(path, d) for d in include_dirs)

    exclude_hit = any(match_dir_prefix(path, d) for d in exclude_dirs)
    return (not include_ok) or exclude_hit


def expand_allowed_targets(
    candidate: Path,
    repo_root: Path,
    includes: list[str],
    excludes: list[str],
) -> list[Path]:
    if not candidate.exists() or not is_path_allowed(candidate, repo_root, includes, excludes):
        return []

    if not candidate.is_dir():
        return [candidate]

    _, relative = relative_parts_and_value(candidate, repo_root)
    nested_excludes: set[str] = set(excludes)
    nested_excludes.update(
        excluded
        for excluded in ALWAYS_EXCLUDED_DIRS
        if excluded.strip().rstrip("/").startswith(f"{relative}/")
    )
    has_nested_excludes = any(
        excluded != relative and match_dir_prefix(excluded, relative)
        for excluded in nested_excludes
    )
    if not has_nested_excludes:
        return [candidate]

    expanded: list[Path] = []
    for child in sorted(candidate.iterdir()):
        expanded.extend(expand_allowed_targets(child, repo_root, includes, excludes))
    return expanded


def filter_paths_with_env_dirs(paths: list[Path], repo_root: Path) -> list[Path]:
    include_dirs, exclude_dirs = env_include_exclude_dirs()

    if not include_dirs and not exclude_dirs:
        return paths

    return [
        path
        for path in paths
        if is_path_allowed(path, repo_root, include_dirs, exclude_dirs)
    ]


def build_filtered_file_list(include_csv: str, exclude_csv: str) -> list[str]:
    from .file import git_tracked_files

    include_dirs = csv_dirs(include_csv) if include_csv else []
    exclude_dirs = csv_dirs(exclude_csv) if exclude_csv else []

    filtered: list[str] = []
    for file in git_tracked_files():
        include_ok = True
        if include_dirs:
            include_ok = any(match_dir_prefix(file, d) for d in include_dirs)

        exclude_hit = any(match_dir_prefix(file, d) for d in exclude_dirs)

        if include_ok and not exclude_hit:
            filtered.append(file)

    return filtered


def strip_all_files_args(args: list[str]) -> list[str]:
    return [arg for arg in args if arg not in {"-a", "--all-files"}]


class PathPolicy:
    """Single source of truth for include/exclude dirs for all runners."""

    def __init__(self, include_dirs: str, exclude_dirs: str) -> None:
        self.include_dirs = include_dirs
        self.exclude_dirs = exclude_dirs

    @classmethod
    def from_env(cls, hooks_dir: Path, env: dict[str, str]) -> "PathPolicy":
        del hooks_dir

        source_dirs = ",".join(PYTHON_SOURCE_DIRS)
        module_dirs = ",".join(MODULE_SEARCH_DIRS)
        excluded_dirs = ",".join(sorted(ALWAYS_EXCLUDED_DIRS))

        default_include = _csv_unique(".", source_dirs, module_dirs)
        default_exclude = _csv_unique(excluded_dirs)

        include_dirs = (
            env.get("QUALITY_GATE_INCLUDE_DIRS", "").strip()
            or env.get("PCR_INCLUDE_DIRS", "").strip()
            or default_include
        )
        exclude_dirs = (
            env.get("QUALITY_GATE_EXCLUDE_DIRS", "").strip()
            or env.get("PCR_EXCLUDE_DIRS", "").strip()
            or default_exclude
        )

        return cls(_csv_unique(include_dirs), _csv_unique(exclude_dirs))

    def apply(self, env: dict[str, str]) -> None:
        env["QUALITY_GATE_INCLUDE_DIRS"] = self.include_dirs
        env["QUALITY_GATE_EXCLUDE_DIRS"] = self.exclude_dirs
        env["PCR_INCLUDE_DIRS"] = self.include_dirs
        env["PCR_EXCLUDE_DIRS"] = self.exclude_dirs
