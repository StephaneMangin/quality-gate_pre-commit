from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .path import VENV_DIR_NAMES


def resolve_tool(name: str, env: dict[str, str]) -> str | None:
    return shutil.which(name, path=env.get("PATH"))


def resolve_precommit(env: dict[str, str]) -> str | None:
    return resolve_tool("pre-commit", env)


def resolve_python(env: dict[str, str]) -> str | None:
    return resolve_tool("python3", env) or resolve_tool("python", env)


def get_venv_bin_dir(repo_root: Path) -> Path | None:
    for venv_name in VENV_DIR_NAMES:
        venv_path = repo_root / venv_name
        if venv_path.exists():
            bin_dir = venv_path / "bin"
            if bin_dir.exists():
                return bin_dir
    return None


def tool_cmd(name: str, repo_root: Path | None = None) -> list[str]:
    if repo_root:
        venv_bin = get_venv_bin_dir(repo_root)
        if venv_bin:
            tool_path = venv_bin / name
            if tool_path.exists():
                return [str(tool_path)]

    tool = shutil.which(name)
    if tool:
        return [tool]

    return [sys.executable, "-m", name]
