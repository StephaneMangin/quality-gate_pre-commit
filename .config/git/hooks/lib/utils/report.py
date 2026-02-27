from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    blocking: bool
    details: str = ""


def is_blocking(mode: str, check_name: str) -> bool:
    normalized = (mode or "hybrid").strip().lower()
    if normalized == "info":
        return False
    if normalized == "strict":
        return True
    return check_name in {"complexity", "dead code", "module dependencies"}


def render_summary(results: list[CheckResult]) -> tuple[int, int]:
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    return passed, failed
