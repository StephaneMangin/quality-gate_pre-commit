from __future__ import annotations

import os

from .config import load_settings, setup_logging
from .output import log, print_summary
from .runner import run_checks
from lib.utils.display import box_title
from lib.utils.env import repo_root as get_repo_root
from lib.utils.quality import (
    detect_python_project,
    ensure_tools_installed,
    iter_python_targets,
    staged_files,
)


def main() -> int:
    setup_logging()
    settings = load_settings()

    repo_root = get_repo_root()
    os.chdir(repo_root)

    if settings.report_level == "full":
        box_title("Q U A L I T Y   G A T E")
        log(f"[quality-gate] mode={settings.mode}\n")

    ensure_tools_installed(repo_root)

    staged = staged_files(repo_root)
    if not staged and settings.no_staged_mode == "skip":
        log("[quality-gate] Aucun fichier staged, skip.")
        return 0

    if not detect_python_project(repo_root, staged):
        log("[quality-gate] Projet non-Python détecté, skip.")
        return 0

    targets = iter_python_targets(repo_root, staged)
    if settings.report_level == "full":
        log(f"[quality-gate] targets={', '.join(targets)}\n")

    results = run_checks(repo_root, targets, settings)
    any_failed, any_blocking_failed = print_summary(results, settings)

    if any_blocking_failed:
        return 1
    if not any_failed:
        log("[quality-gate] Tous les checks sont OK.")
    return 0
