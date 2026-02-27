from __future__ import annotations

from typing import Iterable

from .config import Settings
from lib.utils.display import section_title
from lib.utils.report import CheckResult


def log(message: str = "") -> None:
    print(message)


def print_summary(results: Iterable[CheckResult], settings: Settings) -> tuple[bool, bool]:
    results_list = list(results)
    any_failed = False
    any_blocking_failed = False

    if settings.report_level == "full":
        section_title("SUMMARY")

    for result in results_list:
        status = "✓" if result.passed else "✗"
        log(f"    {status}  {result.name:<25} ({result.details})")
        if not result.passed:
            any_failed = True
            if result.blocking:
                any_blocking_failed = True

    if settings.report_level == "full":
        log("\n  ══════════════════════════════════════")
        if any_blocking_failed:
            log("  ✗  QUALITY GATES FAILED")
        else:
            log("  ✓  ALL QUALITY GATES PASSED")
        log("  ══════════════════════════════════════\n")

    return any_failed, any_blocking_failed
