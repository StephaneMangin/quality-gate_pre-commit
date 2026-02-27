#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def _hooks_root_dir() -> Path:
    """Return hooks root directory (~/.config/git/hooks equivalent)."""
    return Path(__file__).resolve().parents[1]


def _load_search_path_config() -> dict[str, str]:
    """Load simple KEY=VALUE config for search paths (VALUE as CSV)."""
    config: dict[str, str] = {}
    config_file = _hooks_root_dir() / "configs" / "search-paths.conf"
    if not config_file.exists():
        return config

    for raw_line in config_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        config[key.strip()] = value.strip()
    return config


_SEARCH_PATH_CONFIG = _load_search_path_config()


def _config_csv(key: str, default: list[str]) -> list[str]:
    """Read CSV list from shared config with fallback default values."""
    raw = _SEARCH_PATH_CONFIG.get(key, "")
    if not raw:
        return list(default)

    values: list[str] = []
    seen: set[str] = set()
    for token in raw.split(","):
        value = token.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values or list(default)


VENV_DIR_NAMES = tuple(_config_csv("VENV_DIRS", [".venv", "venv", ".env"]))
PYTHON_SOURCE_DIRS = tuple(_config_csv("PYTHON_SOURCE_DIRS", ["src", "app"]))
MODULE_SEARCH_DIRS = tuple(
    _config_csv("MODULE_SEARCH_DIRS", ["src", "addons", "modules"])
)
ALWAYS_EXCLUDED_DIRS = set(
    _config_csv(
        "SEARCH_EXCLUDED_DIRS",
        [
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
        ],
    )
)


def _run(cmd: list[str], cwd: Path) -> tuple[str, str, int]:
    """Execute a command and return (stdout, stderr, return_code)."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.stdout, proc.stderr, proc.returncode


def _get_venv_bin_dir(repo_root: Path) -> Path | None:
    """Detect the bin directory of the project's virtual environment."""
    for venv_name in VENV_DIR_NAMES:
        venv_path = repo_root / venv_name
        if venv_path.exists():
            bin_dir = venv_path / "bin"
            if bin_dir.exists():
                return bin_dir
    return None


def _tool_cmd(name: str, repo_root: Path | None = None) -> list[str]:
    """Resolve a tool command with fallback chain (venv > PATH > python -m)."""
    if repo_root:
        venv_bin = _get_venv_bin_dir(repo_root)
        if venv_bin:
            tool_path = venv_bin / name
            if tool_path.exists():
                return [str(tool_path)]

    tool = shutil.which(name)
    if tool:
        return [tool]

    return [sys.executable, "-m", name]


def _repo_root() -> Path:
    """Return the Git repository root directory (or current cwd fallback)."""
    out, _, rc = _run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    if rc != 0:
        return Path.cwd()
    return Path(out.strip())


def _ensure_tools_installed(repo_root: Path) -> None:
    """Verify required tools are available; warn if missing."""
    required_tools = {
        "radon": "radon",
        "vulture": "vulture",
        "coverage": "coverage",
    }

    missing = []

    for module_name, pip_name in required_tools.items():
        venv_bin = _get_venv_bin_dir(repo_root)
        if venv_bin:
            tool_path = venv_bin / module_name
            if tool_path.exists():
                continue

        if shutil.which(module_name):
            continue

        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {module_name}"],
                timeout=1,
                capture_output=True,
            )
            if result.returncode == 0:
                continue
        except Exception:
            pass

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
        "[quality-gate]   (Checks for missing tools will be skipped)\n", file=sys.stderr
    )


def _staged_files(repo_root: Path) -> list[Path]:
    """List files staged for commit."""
    out, _, rc = _run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
        repo_root,
    )
    if rc != 0:
        return []
    return [repo_root / line.strip() for line in out.splitlines() if line.strip()]


def _parse_dir_csv_env(var_name: str) -> list[str]:
    """Parse CSV dirs from env var into normalized relative directory strings."""
    raw = os.getenv(var_name, "")
    values: list[str] = []
    seen: set[str] = set()

    for token in raw.split(","):
        value = token.strip()
        if value.startswith("./"):
            value = value[2:]
        value = value.rstrip("/")
        if not value or value == ".":
            continue
        if value not in seen:
            seen.add(value)
            values.append(value)
    return values


def _env_include_exclude_dirs() -> tuple[list[str], list[str]]:
    """Return (include_dirs, exclude_dirs) from quality gate env filters."""
    include_dirs = _parse_dir_csv_env("QUALITY_GATE_INCLUDE_DIRS")
    exclude_dirs = _parse_dir_csv_env("QUALITY_GATE_EXCLUDE_DIRS")
    return include_dirs, exclude_dirs


def _matches_dir_prefix(relative_path: str, directory: str) -> bool:
    """Return True if path is equal to directory or inside it."""
    return relative_path == directory or relative_path.startswith(f"{directory}/")


def _is_path_allowed(
    path: Path, repo_root: Path, includes: list[str], excludes: list[str]
) -> bool:
    """Filter path using include/exclude directory prefixes."""
    try:
        relative_path = path.relative_to(repo_root)
        relative = str(relative_path).lstrip("./")
    except ValueError:
        relative_path = path
        relative = str(path)

    if any(part in ALWAYS_EXCLUDED_DIRS for part in relative_path.parts):
        return False

    if any(_matches_dir_prefix(relative, excluded) for excluded in excludes):
        return False
    if includes and not any(
        _matches_dir_prefix(relative, included) for included in includes
    ):
        return False
    return True


def _filter_paths_with_env_dirs(paths: list[Path], repo_root: Path) -> list[Path]:
    """Filter paths using QUALITY_GATE_INCLUDE_DIRS/QUALITY_GATE_EXCLUDE_DIRS."""
    include_dirs, exclude_dirs = _env_include_exclude_dirs()

    if not include_dirs and not exclude_dirs:
        return paths

    return [
        path
        for path in paths
        if _is_path_allowed(path, repo_root, include_dirs, exclude_dirs)
    ]


def _collect_python_files(repo_root: Path, include_hidden: bool = True) -> list[Path]:
    """Collect Python files with global exclusions + env include/exclude filters."""
    py_files = _collect_files(
        repo_root,
        patterns=["*.py"],
        exclude_dirs=ALWAYS_EXCLUDED_DIRS,
        include_hidden=include_hidden,
    )
    return _filter_paths_with_env_dirs(py_files, repo_root)


def _vulture_exclude_csv() -> str:
    """Build vulture --exclude CSV by merging technical and env exclude dirs."""
    _, exclude_dirs = _env_include_exclude_dirs()
    merged: list[str] = []
    seen: set[str] = set()

    for value in [*sorted(ALWAYS_EXCLUDED_DIRS), *exclude_dirs]:
        normalized = value.rstrip("/")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(normalized)

    return ",".join(merged)


def _detect_python_project(repo_root: Path, staged: list[Path]) -> bool:
    """Heuristically detect if repository is a Python project."""
    markers = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "tox.ini"]
    if any((repo_root / marker).exists() for marker in markers):
        return True
    if any(path.suffix == ".py" for path in staged):
        return True
    return bool(_collect_python_files(repo_root, include_hidden=True))


def _iter_python_targets(repo_root: Path, staged: list[Path]) -> list[str]:
    """Build list of Python source targets for analysis."""
    include_dirs = _parse_dir_csv_env("QUALITY_GATE_INCLUDE_DIRS")
    exclude_dirs = _parse_dir_csv_env("QUALITY_GATE_EXCLUDE_DIRS")

    targets: list[Path] = []
    for dirname in PYTHON_SOURCE_DIRS:
        candidate = repo_root / dirname
        if candidate.exists() and _is_path_allowed(
            candidate, repo_root, include_dirs, exclude_dirs
        ):
            targets.append(candidate)

    staged_py = [path for path in staged if path.suffix == ".py" and path.exists()]
    targets.extend(
        path
        for path in staged_py
        if "tests" not in path.parts
        and _is_path_allowed(path, repo_root, include_dirs, exclude_dirs)
    )

    if include_dirs and not targets:
        for directory in include_dirs:
            candidate = repo_root / directory
            if candidate.exists() and _is_path_allowed(
                candidate, repo_root, include_dirs, exclude_dirs
            ):
                targets.append(candidate)

    if not targets:
        if include_dirs:
            for candidate in repo_root.iterdir():
                if _is_path_allowed(candidate, repo_root, include_dirs, exclude_dirs):
                    targets.append(candidate)
        elif exclude_dirs:
            for candidate in repo_root.iterdir():
                if _is_path_allowed(candidate, repo_root, include_dirs, exclude_dirs):
                    targets.append(candidate)
        else:
            targets = [repo_root]

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


def _box_title(title: str) -> None:
    """Print section title in ASCII box."""
    width = 70
    print(f"┌{'─' * width}┐")
    print(f"│ {title.center(width - 2)} │")
    print(f"└{'─' * width}┘\n")


def _section_title(title: str) -> None:
    """Print section title."""
    width = 70
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}\n")


def _bar_chart(label: str, count: int, total: int, width: int = 30) -> str:
    """Create a simple text bar chart."""
    if total == 0:
        filled = 0
        pct = 0.0
    else:
        filled = int((count / total) * width)
        pct = count / total * 100
    bar = "█" * filled + "░" * (width - filled)
    return f"    {label:<20} {bar} {count:3d} ({pct:5.1f}%)"


class ProgressReporter:
    """Progress reporter for file scans.

    - En TTY: met à jour une seule ligne
    - Hors TTY (logs/CI): imprime une ligne par update
    """

    def __init__(
        self,
        total: int,
        enabled: bool,
        prefix: str = "[scan]",
        every: int = 1,
    ) -> None:
        self.total = max(total, 0)
        self.enabled = bool(enabled) and self.total > 0
        self.prefix = prefix
        self.every = max(int(every), 1)
        self._is_tty = sys.stdout.isatty()
        self._last_len = 0

    def update(
        self, index: int, file_path: Path, repo_root: Path | None = None
    ) -> None:
        if not self.enabled:
            return
        if index != self.total and index % self.every != 0:
            return

        shown = file_path
        if repo_root is not None:
            try:
                shown = file_path.relative_to(repo_root)
            except Exception:
                shown = file_path

        pct = (index / self.total) * 100
        msg = f"{self.prefix} {index}/{self.total} ({pct:5.1f}%) file: {shown}"

        if self._is_tty:
            padded = msg.ljust(max(self._last_len, len(msg)))
            print(f"\r{padded}", end="", flush=True)
            self._last_len = len(padded)
        else:
            print(msg)

    def close(self) -> None:
        if self.enabled and self._is_tty:
            print()


def _collect_files(
    root_dir: Path,
    patterns: Iterable[str],
    exclude_dirs: set[str] | None = None,
    include_hidden: bool = False,
) -> list[Path]:
    """Collect files from root_dir using glob patterns with generic filtering."""
    exclude_dirs = exclude_dirs or ALWAYS_EXCLUDED_DIRS

    found: list[Path] = []
    seen: set[Path] = set()

    for pattern in patterns:
        for path in root_dir.rglob(pattern):
            if not path.is_file():
                continue

            rel_parts = path.relative_to(root_dir).parts
            if any(part in exclude_dirs for part in rel_parts):
                continue

            if not include_hidden and any(part.startswith(".") for part in rel_parts):
                continue

            if path in seen:
                continue
            seen.add(path)
            found.append(path)

    return sorted(found)


def _iter_with_progress(
    files: list[Path],
    repo_root: Path,
    enabled: bool,
    prefix: str,
    every: int,
):
    """Yield files while displaying progress information."""
    reporter = ProgressReporter(
        total=len(files),
        enabled=enabled,
        prefix=prefix,
        every=every,
    )
    try:
        for index, file_path in enumerate(files, start=1):
            reporter.update(index, file_path, repo_root)
            yield file_path
    finally:
        reporter.close()
