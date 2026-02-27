from __future__ import annotations

import shutil
from pathlib import Path

from .process import run_cmd


def repo_root() -> Path:
    out, _, rc = run_cmd(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    if rc == 0:
        root = out.strip()
        if root:
            return Path(root)
    return Path.cwd()


def load_env_overrides(env: dict[str, str], root: Path) -> None:
    env_file = Path(env.get("PROJECT_ENV_FILE", str(root / ".env")))
    if not env_file.is_file():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue
        if not (key.startswith("QUALITY_GATE_") or key.startswith("PCR_")):
            continue
        if key in env:
            continue

        if len(value) >= 2 and (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ):
            value = value[1:-1]

        env[key] = value


def activate_repo_venv(env: dict[str, str], root: Path) -> None:
    for name in (".venv", "venv", ".env"):
        bin_dir = root / name / "bin"
        if not bin_dir.is_dir():
            continue

        current_path = env.get("PATH", "")
        env["PATH"] = f"{bin_dir}:{current_path}" if current_path else str(bin_dir)
        env["VIRTUAL_ENV"] = str(bin_dir.parent)
        return


def resolve_on_path(binary: str, env: dict[str, str]) -> str | None:
    return shutil.which(binary, path=env.get("PATH"))
