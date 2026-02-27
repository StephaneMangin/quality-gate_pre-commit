from __future__ import annotations

import time
from pathlib import Path

from .check_complexity import check_complexity
from .check_coverage import check_coverage
from .check_dead_code import check_dead_code
from .check_dependencies import check_module_dependencies
from .check_maintainability import check_maintainability
from .config import Settings
from .output import log
from lib.utils.display import section_title
from lib.utils.report import CheckResult


def run_check_timed(runner) -> tuple[CheckResult, float]:
    started = time.perf_counter()
    result = runner()
    return result, time.perf_counter() - started


def build_checks(repo_root: Path, targets: list[str], settings: Settings):
    return [
        ("module dependencies", lambda: check_module_dependencies(repo_root, settings)),
        ("complexity", lambda: check_complexity(repo_root, targets, settings)),
        ("maintainability", lambda: check_maintainability(repo_root, targets, settings)),
        ("dead code", lambda: check_dead_code(repo_root, targets, settings)),
        ("coverage", lambda: check_coverage(repo_root, settings)),
    ]


def run_checks(repo_root: Path, targets: list[str], settings: Settings) -> list[CheckResult]:
    checks = build_checks(repo_root, targets, settings)
    results: list[CheckResult] = []
    timings: list[tuple[str, float]] = []

    for check_name, runner in checks:
        result, elapsed = run_check_timed(runner)
        results.append(result)
        timings.append((check_name, elapsed))

    if settings.timing_enabled and settings.report_level == "full":
        section_title("CHECK TIMINGS")
        total = sum(duration for _, duration in timings)
        for check_name, duration in sorted(timings, key=lambda item: item[1], reverse=True):
            log(f"    {check_name:<25} {duration:7.3f}s")
        log(f"\n    {'TOTAL':<25} {total:7.3f}s\n")

    return results
