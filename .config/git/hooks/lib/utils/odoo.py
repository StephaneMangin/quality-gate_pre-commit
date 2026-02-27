from __future__ import annotations

import os
from pathlib import Path

from .file import git_staged_files
from .path import is_path_filtered_out


def is_manifest_project(include_csv: str = "", exclude_csv: str = "") -> bool:
    if not include_csv:
        include_csv = os.environ.get("QUALITY_GATE_INCLUDE_DIRS", "")
    if not exclude_csv:
        exclude_csv = os.environ.get("QUALITY_GATE_EXCLUDE_DIRS", "")
    root = Path.cwd()
    max_depth = 4

    for path in root.rglob("__manifest__.py"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        rel_str = rel.as_posix()
        if is_path_filtered_out(rel_str, include_csv, exclude_csv):
            continue
        if len(rel.parts) <= max_depth:
            return True
    return False


def module_from_file(file_path: str) -> str | None:
    path = Path(file_path)
    for dir_path in (path.parent, *path.parent.parents):
        if dir_path.as_posix() in {".", "/"}:
            continue
        if (dir_path / "__manifest__.py").is_file():
            return dir_path.name
    return None


def changed_modules(include_csv: str = "", exclude_csv: str = "") -> list[str]:
    if not include_csv:
        include_csv = os.environ.get("QUALITY_GATE_INCLUDE_DIRS", "")
    if not exclude_csv:
        exclude_csv = os.environ.get("QUALITY_GATE_EXCLUDE_DIRS", "")
    modules: set[str] = set()
    for file in git_staged_files():
        file_path = Path(file).as_posix()
        if is_path_filtered_out(file_path, include_csv, exclude_csv):
            continue
        module = module_from_file(file)
        if module:
            modules.add(module)
    return sorted(modules)
